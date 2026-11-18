// @vitest-environment jsdom
// Iteraciones 71 y 76 · revisión de productos por foto (el detector corre a pedido desde la 76)
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { PhotoProductReview } from './PhotoProductReview';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

let host: HTMLDivElement;
let root: Root;
const confirm = vi.fn();
beforeEach(async () => {
  vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:photo'), revokeObjectURL: vi.fn() });
  confirm.mockReset();
  confirm.mockResolvedValue(true);
  vi.mocked(api.post).mockReset();
  host = document.createElement('div');
  document.body.append(host);
  root = createRoot(host);
  await act(async () => root.render(createElement(PhotoProductReview, { onConfirm: confirm })));
});
afterEach(async () => {
  await act(async () => root.unmount());
  host.remove();
  vi.unstubAllGlobals();
});

async function upload() {
  const input = host.querySelector<HTMLInputElement>('input[type=file]')!;
  const file = new File(['foto'], 'bolsa.jpg', { type: 'image/jpeg' });
  Object.defineProperty(input, 'files', { configurable: true, value: [file] });
  await act(async () => input.dispatchEvent(new Event('change', { bubbles: true })));
  return file;
}
const byText = (text: string) => [...host.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent === text)!;
const suggest = async () => act(async () => byText('Sugerir con el detector').click()); // S-369, S-373
const save = () => host.querySelector<HTMLButtonElement>('.primary-button')!;
async function quantity(value: string) {
  const input = host.querySelector<HTMLInputElement>('input[type=number]')!;
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, value);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
}

it('corrige el conteo y confirma con la misma foto, sin guardar solo', async () => {
  vi.mocked(api.post).mockResolvedValue({ productos: [{ producto: 'zanahoria', cantidad: 3, confianza: 0.6 }] });
  const file = await upload();
  expect(api.post).not.toHaveBeenCalled();
  await suggest();
  expect(confirm).not.toHaveBeenCalled();
  await quantity('2');
  await act(async () => save().click());
  expect(confirm).toHaveBeenCalledWith(file, [{ producto: 'zanahoria', cantidad: 2, confianza: undefined }]);
  expect(host.textContent).toContain('Confirmado por ti');
  expect(host.querySelector<HTMLInputElement>('input[type=number]')!.disabled).toBe(true);
  await act(async () => save().click());
  expect(confirm).toHaveBeenCalledTimes(1);
});

it('si el detector falla se revisa a mano y no acepta cantidades inválidas', async () => {
  vi.mocked(api.post).mockRejectedValue(new Error('Análisis no instalado'));
  await upload();
  await suggest();
  await act(async () => byText('Añadir producto manualmente').click());
  await quantity('0');
  expect(save().disabled).toBe(true);
  await quantity('1');
  expect(save().disabled).toBe(false);
});

it('conserva las correcciones si guardar falla', async () => {
  vi.mocked(api.post).mockResolvedValue({ productos: [{ producto: 'ajo', cantidad: 2 }] });
  confirm.mockResolvedValue(false);
  await upload();
  await suggest();
  await act(async () => save().click());
  expect(host.querySelector<HTMLInputElement>('input[type=number]')!.value).toBe('2');
  expect(host.textContent).not.toContain('Confirmado por ti');
});

it('ignora la respuesta de una foto anterior al elegir otra', async () => {
  let resolve!: (value: unknown) => void;
  vi.mocked(api.post)
    .mockImplementationOnce(() => new Promise((r) => { resolve = r; }) as never)
    .mockResolvedValueOnce({ productos: [{ producto: 'cebolla', cantidad: 1 }] });
  await upload();
  await suggest();
  await upload();
  await suggest();
  await act(async () => resolve({ productos: [{ producto: 'papa', cantidad: 8 }] }));
  expect(host.querySelector<HTMLSelectElement>('select')!.value).toBe('cebolla');
});

it('exige elegir la variedad de papa y confirmar la fila antes de guardar', async () => {
  const candidates = [{ id: 'PAPA-AMARILLA', name: 'Papa amarilla', unit: 'kg' }, { id: 'PAPA-BLANCA', name: 'Papa blanca', unit: 'kg' }];
  vi.mocked(api.post).mockResolvedValue({ productos: [{ producto: 'papa', cantidad: 3 }] });
  await act(async () => root.render(createElement(PhotoProductReview, { onConfirm: confirm, candidates })));
  await upload();
  await suggest();
  expect(host.querySelector<HTMLSelectElement>('select')!.value).toBe('');
  expect(save().disabled).toBe(true);
  await act(async () => {
    const select = host.querySelector('select')!;
    select.value = 'PAPA-BLANCA';
    select.dispatchEvent(new Event('change', { bubbles: true }));
  });
  await act(async () => host.querySelector<HTMLButtonElement>('[aria-label="Confirmar producto 1"]')!.click());
  await act(async () => save().click());
  expect(confirm.mock.calls[0][1][0]).toMatchObject({ codigo: 'PAPA-BLANCA', cantidad: 3, confirmado: true });
});

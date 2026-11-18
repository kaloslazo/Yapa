// @vitest-environment jsdom
// Iteración 72 · stock confirmado por cargas. Spec: api/docs/desarrollo/72-stock-confirmado.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { SupplierStock } from './SupplierStock';
import { SupplierListEditor } from './SupplierListEditor';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

let host: HTMLDivElement;
let root: Root;
beforeEach(() => {
  host = document.createElement('div');
  document.body.append(host);
  root = createRoot(host);
  vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:photo'), revokeObjectURL: vi.fn() });
});
afterEach(async () => {
  await act(async () => root.unmount());
  host.remove();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

const LIST = 'PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,40,SUP-FRESCOS,0,3.60';
const typeIn = async (input: HTMLInputElement, value: string) => act(async () => {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, value);
  input.dispatchEvent(new Event('input', { bubbles: true }));
});
const click = async (button: HTMLButtonElement) => act(async () => button.click());
const byText = (text: string) => [...host.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent === text)!;

it('ST72-G · pide el peso, confirma la carga y pasa el total vendible al borrador', async () => {
  const apply = vi.fn();
  vi.mocked(api.get).mockResolvedValue({ productos: [] });
  vi.mocked(api.post)
    .mockResolvedValueOnce({ productos: [{ producto: 'papa', cantidad: 3 }] })
    .mockResolvedValueOnce({ productos: [{ id: 'PAPA-AMARILLA', nombre: 'Papa amarilla', cantidad: '2.5', disponible: '2', unidades: 3, unidad: 'kg' }] });
  await act(async () => root.render(createElement(SupplierStock, {
    cycle: '2026-W40', candidates: [{ id: 'PAPA-AMARILLA', name: 'Papa amarilla', unit: 'kg' }], onApply: apply,
  })));
  const file = host.querySelector('input[type=file]')!;
  Object.defineProperty(file, 'files', { value: [new File(['x'], 'foto.jpg', { type: 'image/jpeg' })] });
  await act(async () => file.dispatchEvent(new Event('change', { bubbles: true })));
  await click(byText('Sugerir con el detector')); // iteración 76 (S-373): el detector corre a pedido
  const check = () => host.querySelector<HTMLButtonElement>('[aria-label="Confirmar producto 1"]')!;
  expect(check().disabled).toBe(true); // sin peso no se confirma
  await typeIn(host.querySelectorAll<HTMLInputElement>('input[type=number]')[1], '2.5');
  await click(check());
  await click(host.querySelector<HTMLButtonElement>('.primary-button')!);
  expect(api.post).toHaveBeenLastCalledWith('/api/proveedor/stock/confirmar', expect.any(FormData));
  expect(apply.mock.calls[0][0][0].disponible).toBe('2');
  expect(host.textContent).toContain('3 unidades visibles');
});

it('ST72-H · los precios por volumen de cada producto empiezan cerrados', async () => {
  await act(async () => root.render(createElement(SupplierListEditor, {
    initialText: `${LIST}\nAJO,Ajo,FRESCOS,kg,0.25,40,SUP-FRESCOS,0,4.80`, busy: false, resubmit: false, onSubmit: vi.fn(),
  })));
  expect(host.querySelectorAll('.supplier-volume')).toHaveLength(2);
  expect(host.querySelectorAll('.supplier-volume[open]')).toHaveLength(0);
});

it('ST72-I · recupera el stock por producto sin pasar kilos a unidades', async () => {
  vi.mocked(api.get).mockResolvedValue({ productos: [
    { id: 'PAPA-AMARILLA', nombre: 'Papa amarilla', cantidad: '4', disponible: '4', unidades: 5, unidad: 'kg' },
    { id: 'AJO', nombre: 'Ajo', cantidad: '2', disponible: '2', unidades: 3, unidad: 'kg' },
  ] });
  await act(async () => root.render(createElement(SupplierListEditor, {
    cycle: '2026-W40', initialText: `${LIST}\nAJO,Ajo,FRESCOS,unidad,1,40,SUP-FRESCOS,0,4.80`, busy: false, resubmit: false, onSubmit: vi.fn(),
  })));
  expect(host.querySelector<HTMLInputElement>('[aria-label="Cantidad disponible (kg), producto 1"]')!.value).toBe('4');
  expect(host.querySelector<HTMLInputElement>('[aria-label="Cantidad disponible (unidades), producto 2"]')!.value).toBe('40');
  expect(host.querySelector('[role=alert]')!.textContent).toContain('unidad distinta');
});

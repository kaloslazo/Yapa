// @vitest-environment jsdom
// Iteración 77 · revisar la bolsa con IA que conoce el pedido (VB-J). Spec: api/docs/desarrollo/77-revision-de-bolsas-con-ia.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { PhotoProductReview } from './PhotoProductReview';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

let host: HTMLDivElement;
let root: Root;
const candidates = [{ id: 'PAPA-AMARILLA', name: 'Papa amarilla', unit: 'kg' }, { id: 'PAPA-BLANCA', name: 'Papa blanca', unit: 'kg' }];

beforeEach(() => {
  vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:photo'), revokeObjectURL: vi.fn() });
  host = document.createElement('div');
  document.body.append(host);
  root = createRoot(host);
});
afterEach(async () => {
  await act(async () => root.unmount());
  host.remove();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

async function review(answer: unknown) {
  vi.mocked(api.post).mockResolvedValue(answer as never);
  const photo = new File(['foto'], 'bolsa.jpg', { type: 'image/jpeg' });
  await act(async () => root.render(createElement(PhotoProductReview, { candidates, photo, context: { pedido: '110' }, onConfirm: vi.fn() })));
  await act(async () => [...host.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent === 'Sugerir con el detector')!.click());
}

it('VB-J · con código de la IA la fila llega con el producto elegido, dice de dónde salió y lo que también se ve', async () => {
  await review({ fuente: 'ia', productos: [{ codigo: 'PAPA-BLANCA', nombre: 'Papa blanca', producto: 'papa', cantidad: 3 }], otros: ['tomate'] });
  expect(host.querySelector<HTMLSelectElement>('.photo-product-row select')!.value).toBe('PAPA-BLANCA');
  expect(host.querySelector<HTMLInputElement>('.photo-product-row input[type=number]')!.value).toBe('3');
  expect(host.textContent).toContain('Con IA');
  expect(host.textContent).toContain('También se ve: tomate');
  const form = vi.mocked(api.post).mock.calls[0][1] as FormData;
  expect(form.get('pedido')).toBe('110');
  expect(form.get('foto_archivo')).toBeInstanceOf(File);
});

it('VB-J · si respondió el detector local, lo dice', async () => {
  await review({ fuente: 'detector', productos: [{ producto: 'papa', cantidad: 2, confianza: 0.8 }] });
  expect(host.textContent).toContain('Con el detector local');
  expect(host.querySelector<HTMLSelectElement>('.photo-product-row select')!.value).toBe(''); // dos papas: se elige a mano
});

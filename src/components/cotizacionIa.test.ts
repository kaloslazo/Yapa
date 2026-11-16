// @vitest-environment jsdom
// Iteración 69 · La cotización del proveedor leída con IA (LP-K). Spec: api/docs/desarrollo/69-lista-del-proveedor-con-ia.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { SupplierListEditor } from './SupplierListEditor';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
afterEach(async () => { if (root) await act(async () => root.unmount()); host?.remove(); vi.clearAllMocks(); });

const LIST = 'PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,400,SUP-FRESCOS,0,3.60';
const READ = {
  fuente: 'ia', nuevos: ['PAPA-HUAYRO'], avisos: ['Lejía: es un producto de otro proveedor, no se agregó.'],
  filas: [
    { codigo: 'PAPA-AMARILLA', nombre: 'Papa amarilla', categoria: 'FRESCOS', unidad: 'kg', paso: '1', maximo: '300', tramos: [{ desde: '0', precio: '3.40' }, { desde: '100', precio: '3.10' }] },
    { codigo: 'PAPA-HUAYRO', nombre: 'Papa huayro', categoria: 'FRESCOS', unidad: 'kg', paso: '1', maximo: '0', tramos: [{ desde: '0', precio: '4.20' }] },
  ],
};

describe('LP-K · leer la cotización con IA llena el borrador', () => {
  it('actualiza lo que ya vende, agrega lo nuevo y queda como borrador sin enviar', async () => {
    vi.mocked(api.post).mockResolvedValue(READ as never);
    const submit = vi.fn().mockResolvedValue(true);
    host = document.createElement('div'); document.body.append(host); root = createRoot(host);
    await act(async () => { root.render(createElement(SupplierListEditor, { initialText: LIST, busy: false, onSubmit: submit, resubmit: false })); });
    const area = host.querySelector<HTMLTextAreaElement>('.quote-reader textarea')!;
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!.call(area, 'Papa amarilla S/ 3.40');
      area.dispatchEvent(new Event('input', { bubbles: true }));
    });
    const read = [...host.querySelectorAll('button')].find(b => b.textContent?.includes('Leer cotización'))!;
    await act(async () => read.click());
    const sent = vi.mocked(api.post).mock.calls[0];
    expect(sent[0]).toBe('/api/proveedor/lista/leer');
    expect((sent[1] as FormData).get('texto')).toBe('Papa amarilla S/ 3.40');
    expect(host.querySelectorAll('.supplier-product')).toHaveLength(2);
    expect(host.textContent).toContain('Papa huayro');
    expect(host.textContent).toContain('S/ 3.40 / kg');
    expect(host.textContent).toContain('Borrador con cambios sin enviar');
    expect(host.textContent).toContain('1 actualizado y 1 nuevo');
    expect(host.textContent).toContain('Lejía: es un producto de otro proveedor');
    const send = async () => { await act(async () => { host.querySelector('form.supplier-editor')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); }); };
    await send(); // S-348: el producto nuevo llega con máximo 0 y el proveedor tiene que completarlo
    expect(submit).not.toHaveBeenCalled();
    expect(host.querySelector('.supplier-errors')?.textContent).toContain('Producto 2: la cantidad disponible');
    const max = host.querySelector<HTMLInputElement>('input[aria-label="Cantidad disponible (kg), producto 2"]')!;
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(max, '60');
      max.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await send();
    expect(submit.mock.calls[0][0]).toContain('PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,300,SUP-FRESCOS,0,3.40,100,3.10');
    expect(submit.mock.calls[0][0]).toContain('PAPA-HUAYRO,Papa huayro,FRESCOS,kg,1,60,,0,4.20');
  });
});

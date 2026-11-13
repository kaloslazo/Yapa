// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { BagForm } from './BagForm';

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let host: HTMLDivElement;
let root: Root;
const send = vi.fn<(form: FormData) => Promise<boolean>>();
beforeEach(async () => {
  send.mockReset(); send.mockResolvedValue(true);
  host = document.createElement('div'); document.body.append(host); root = createRoot(host);
  await act(async () => root.render(createElement(BagForm, { onSend: send })));
});
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
const button = (name: string) => host.querySelector<HTMLButtonElement>(`button[aria-label="${name}"]`)!;
const inputs = () => [...host.querySelectorAll<HTMLInputElement>('input[type=file]')];
async function click(name: string) { await act(async () => button(name).click()); }
async function photos() {
  await act(async () => inputs().forEach((input, i) => {
    Object.defineProperty(input, 'files', { configurable: true, value: [new File([`foto-${i}`], `bolsa-${i}.png`, { type: 'image/png' })] });
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }));
}
async function submit() { await act(async () => host.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }))); }

it('elige cuántas fotos preparar y nunca baja de una bolsa', async () => {
  expect(inputs()).toHaveLength(1);
  expect(button('Disminuir bolsas').disabled).toBe(true);
  await click('Aumentar bolsas'); expect(inputs()).toHaveLength(2);
  await click('Disminuir bolsas'); expect(inputs()).toHaveLength(1);
  expect(send).not.toHaveBeenCalled();
});
it('exige una foto por bolsa antes de confirmar', async () => {
  await click('Aumentar bolsas');
  expect(inputs().every(input => input.required)).toBe(true);
  expect(button('Confirmar bolsas').disabled).toBe(true);
  await submit(); expect(send).not.toHaveBeenCalled();
});
it('envía dos fotos distintas en orden y reinicia al completar', async () => {
  await click('Aumentar bolsas'); await photos(); await submit();
  expect(send).toHaveBeenCalledTimes(2);
  expect(send.mock.calls.map(([form]) => (form.get('foto_archivo') as File).name)).toEqual(['bolsa-0.png', 'bolsa-1.png']);
  expect(inputs()).toHaveLength(1);
  expect(button('Confirmar bolsas').disabled).toBe(true);
});
it('conserva solo las pendientes tras un fallo y no reenvía la primera', async () => {
  send.mockResolvedValueOnce(true).mockResolvedValueOnce(false).mockResolvedValue(true);
  await click('Aumentar bolsas'); await photos(); await submit();
  expect(inputs()).toHaveLength(1);
  expect(host.textContent).toContain('1 bolsa guardada');
  await submit();
  expect(send.mock.calls.map(([form]) => (form.get('foto_archivo') as File).name)).toEqual(['bolsa-0.png', 'bolsa-1.png', 'bolsa-1.png']);
});
it('bloquea los controles mientras guarda', async () => {
  let finish!: (value: boolean) => void;
  send.mockImplementation(() => new Promise(resolve => { finish = resolve; }));
  await photos(); await submit();
  expect(button('Aumentar bolsas').disabled).toBe(true);
  expect(button('Confirmar bolsas').disabled).toBe(true);
  expect(inputs()[0].disabled).toBe(true);
  await act(async () => finish(true));
  expect(button('Aumentar bolsas').disabled).toBe(false);
});

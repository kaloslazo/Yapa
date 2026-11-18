// @vitest-environment jsdom
// Iteración 73 · preguntas, opciones y última respuesta. Spec: api/docs/desarrollo/73-chat-conversacion.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, expect, it, vi } from 'vitest';
import { FaqChatbot } from './FaqChatbot';
import { api } from '../services/api';

vi.mock('../services/api', async (original) => ({ ...await original<typeof import('../services/api')>(), api: { post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

let root: Root;
let host: HTMLDivElement;
afterEach(async () => {
  await act(async () => root.unmount());
  host.remove();
  vi.clearAllMocks();
});

async function start() {
  host = document.createElement('div');
  document.body.append(host);
  root = createRoot(host);
  await act(async () => root.render(createElement(FaqChatbot)));
  await act(async () => host.querySelector<HTMLButtonElement>('.faq-chat-launcher')!.click());
}

async function ask(text: string) {
  const input = host.querySelector('input')!;
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, text);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await act(async () => host.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })));
}

const button = (text: string) => [...host.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent === text);

it('CH73-A · propone opciones de pagos sin IA y la respuesta queda al final', async () => {
  await start();
  await ask('pagué');
  expect(api.post).not.toHaveBeenCalled();
  expect(host.querySelector('[role=log]')!.textContent).toContain('pagué');
  const option = [...host.querySelectorAll<HTMLButtonElement>('.faq-chat-results button')].find((b) => b.textContent?.includes('Cómo pago'))!;
  expect(option).toBeTruthy();
  await act(async () => option.click());
  expect(host.querySelector('[role=log] article:last-child')!.textContent).toContain('Yape o Plin');
  expect(host.querySelector('.faq-chat-body')!.lastElementChild?.getAttribute('data-chat-bottom')).toBe('true');
});

it('CH73-B · una duda desconocida no inventa respuesta ni llama a un modelo', async () => {
  await start();
  await ask('astronauta galaxia');
  expect(api.post).not.toHaveBeenCalled();
  expect(host.textContent).toContain('No encontré una respuesta segura');
  expect(button('Consultar asistente de compra')).toBeTruthy();
});

it('CH73-C · reiniciar evita que reaparezca una respuesta que estaba en camino', async () => {
  let resolve!: (value: unknown) => void;
  vi.mocked(api.post).mockImplementationOnce(() => new Promise((r) => { resolve = r; }) as never);
  await start();
  await ask('¿Dónde está mi pedido?');
  await act(async () => button('Reiniciar')!.click());
  await act(async () => resolve({ respuesta: 'Respuesta antigua', fuente: 'datos', sugerencias: [] }));
  expect(host.querySelector('[role=log]')!.textContent).toBe('');
});

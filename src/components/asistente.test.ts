// @vitest-environment jsdom
// Iteración 70 · Asistente de compra (AS-K). Spec: api/docs/desarrollo/70-asistente-de-compra.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FaqChatbot } from './FaqChatbot';
import { api, ApiError } from '../services/api';

vi.mock('../services/api', async (original) => ({ ...(await original<typeof import('../services/api')>()), api: { get: vi.fn(), post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
afterEach(async () => { if (root) await act(async () => root.unmount()); host?.remove(); vi.clearAllMocks(); });

async function ask(question: string) {
  host = document.createElement('div'); document.body.append(host); root = createRoot(host);
  await act(async () => { root.render(createElement(FaqChatbot)); });
  await act(async () => host.querySelector<HTMLButtonElement>('.faq-chat-launcher')!.click());
  const input = host.querySelector<HTMLInputElement>('.faq-chat-composer input')!;
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, question);
    input.dispatchEvent(new Event('input', { bubbles: true }));
  });
  await act(async () => { host.querySelector('form.faq-chat-composer')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
}

describe('AS-K · el chat pregunta al asistente', () => {
  it('con sesión, muestra la pregunta y la respuesta con tus datos', async () => {
    vi.mocked(api.post).mockResolvedValue({ respuesta: 'Tu pedido 12: Pago verificado.', tema: 'pedido', fuente: 'datos', sugerencias: [] } as never);
    await ask('¿Dónde está mi pedido?');
    expect(api.post).toHaveBeenCalledWith('/api/asistente', { pregunta: '¿Dónde está mi pedido?' });
    const log = host.querySelector('[role=log]')!.textContent;
    expect(log).toContain('¿Dónde está mi pedido?');
    expect(log).toContain('Tu pedido 12: Pago verificado.');
    expect(host.querySelector('.faq-chat-composer input')!.getAttribute('value') ?? '').toBe('');
  });
  it('sin sesión, pide entrar y deja las preguntas frecuentes', async () => {
    vi.mocked(api.post).mockRejectedValue(new ApiError(401, 'NOT_AUTHENTICATED', 'Entra primero.'));
    await ask('¿Dónde está mi pedido?');
    expect(host.querySelector('[role=log]')!.textContent).toContain('Entra con tu número');
    expect(host.querySelectorAll('.faq-chat-results button').length).toBeGreaterThan(0);
  });
});

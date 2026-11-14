// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { expect, it } from 'vitest';
import { FaqChatbot } from './FaqChatbot';
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
it('abre, responde, reinicia y devuelve el foco al cerrar con Escape', async () => {
  const host = document.createElement('div'); document.body.append(host); const root = createRoot(host);
  try {
    await act(async () => root.render(createElement(FaqChatbot)));
    const launcher = host.querySelector('button')!;
    await act(async () => launcher.click());
    expect(document.activeElement).toBe(host.querySelector('input'));
    await act(async () => host.querySelector<HTMLButtonElement>('.faq-chat-results button')!.click());
    expect(host.querySelector('[role=log]')?.textContent).toContain('Hasta el miércoles');
    await act(async () => host.querySelector<HTMLButtonElement>('.text-button')!.click());
    expect(host.querySelector('[role=log]')?.textContent).toBe('');
    await act(async () => host.querySelector('[role=dialog]')!.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })));
    expect(host.querySelector('[role=dialog]')).toBeNull(); expect(document.activeElement).toBe(launcher);
  } finally { await act(async () => root.unmount()); host.remove(); }
});

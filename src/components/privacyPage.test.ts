// @vitest-environment jsdom
import { createElement } from 'react';
import { act } from 'react';
import { createRoot } from 'react-dom/client';
import { describe, expect, it } from 'vitest';
import { PrivacyPage } from './PrivacyPage';

describe('página de privacidad (PU-G)', () => {
  it('dice qué datos se guardan, para qué, quién los ve y cómo ejercer los derechos', async () => {
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
    const host = document.createElement('div');
    document.body.appendChild(host);
    await act(async () => { createRoot(host).render(createElement(PrivacyPage)); });
    const text = host.textContent ?? '';
    for (const part of ['Qué datos guardamos', 'Para qué los usamos', 'Quién los ve', 'Cuánto tiempo', 'Tus derechos', 'Ley 29733', 'No vendemos tus datos']) expect(text, part).toContain(part);
    expect(host.querySelector('h1')?.textContent).toBe('Cómo cuidamos tus datos');
    expect(host.querySelector('a[href="/"]')).not.toBeNull();
    expect(document.title).toContain('Privacidad');
  });
});

// @vitest-environment jsdom
import { createElement } from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { InvitePage } from './InvitePage';

type Call = { url: string; body: any }; // eslint-disable-line @typescript-eslint/no-explicit-any
const PREVIEW = { zona: 'Edificio Los Álamos', distrito: 'Lince', invita: 'Ana', vecinos: 3, minimo_grupo: 8 };

let root: Root;
let host: HTMLDivElement;
let calls: Call[];
let replies: Record<string, { status: number; body: unknown }>;

const setValue = (input: HTMLInputElement, value: string) => {
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, input.type === 'checkbox' ? 'checked' : 'value')!.set!;
  if (input.type === 'checkbox') { input.click(); return; }
  setter.call(input, value);
  input.dispatchEvent(new Event('input', { bubbles: true }));
};
const field = (label: string) => [...host.querySelectorAll('label.auth-field')].find((l) => l.textContent?.includes(label))!.querySelector('input')!;
const button = (text: string) => [...host.querySelectorAll('button')].find((b) => b.textContent?.includes(text))!;
const flush = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });

async function render(props: Partial<Parameters<typeof InvitePage>[0]> = {}) {
  const onJoined = vi.fn();
  await act(async () => { root.render(createElement(InvitePage, { code: 'abcDEF123', googleClientId: null, signedIn: false, onJoined, onGoHome: vi.fn(), ...props })); });
  await flush();
  return onJoined;
}

beforeEach(() => {
  (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
  calls = [];
  replies = { '/api/invitaciones/abcDEF123': { status: 200, body: PREVIEW } };
  globalThis.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    calls.push({ url, body: init?.body ? JSON.parse(String(init.body)) : null });
    const reply = replies[url] ?? { status: 422, body: { error: { codigo: 'INVITE_NOT_FOUND', mensaje: 'Ese enlace de invitación no existe o ya no vale.' } } };
    return new Response(JSON.stringify(reply.body), { status: reply.status });
  }) as typeof fetch;
  host = document.createElement('div');
  document.body.appendChild(host);
  root = createRoot(host);
});

afterEach(() => { act(() => root.unmount()); host.remove(); });

describe('página de invitación', () => {
  it('muestra quién invita y la zona, sin apellido', async () => {
    await render();
    expect(host.textContent).toContain('Ana te invita');
    expect(host.textContent).toContain('Edificio Los Álamos · Lince');
    expect(host.textContent).toContain('3 vecinos');
  });

  it('un enlace que no vale lo dice claro', async () => {
    replies = {};
    await render();
    expect(host.textContent).toContain('Este enlace no sirve');
  });

  it('no manda nada si falta el celular o el consentimiento', async () => {
    await render();
    await act(async () => { button('Enviarme el código').click(); });
    expect(host.textContent).toContain('9 dígitos');
    await act(async () => { setValue(field('celular'), '987654321'); });
    await act(async () => { button('Enviarme el código').click(); });
    expect(host.textContent).toContain('aceptar');
    expect(calls.filter((c) => c.url.endsWith('/correo'))).toHaveLength(0);
  });

  it('registro con correo: pide el código y luego crea la cuenta con el PIN elegido', async () => {
    replies['/api/invitaciones/abcDEF123/correo'] = { status: 200, body: { enviado: true } };
    replies['/api/invitaciones/abcDEF123/confirmar'] = { status: 200, body: { usuario: 106, nombre: 'Lucía Ramos', rol: 'vecino', csrf: 't' } };
    const onJoined = await render();
    await act(async () => {
      setValue(field('celular'), '987654321');
      setValue(host.querySelector('input[type=checkbox]') as HTMLInputElement, '');
      setValue(field('nombre'), 'Lucía Ramos');
      setValue(field('correo'), 'lucia@correo.pe');
    });
    await act(async () => { button('Enviarme el código').click(); });
    await flush();
    expect(calls.at(-1)).toEqual({ url: '/api/invitaciones/abcDEF123/correo', body: { nombre: 'Lucía Ramos', celular: '987654321', correo: 'lucia@correo.pe', consentimiento: true } });
    expect(host.textContent).toContain('Te mandamos un código');
    await act(async () => { setValue(field('Código'), '123456'); setValue(field('PIN'), '123456'); });
    await act(async () => { button('Crear mi cuenta').click(); });
    expect(host.textContent).toContain('no sea muy fácil');
    await act(async () => { setValue(field('PIN'), '739104'); });
    await act(async () => { button('Crear mi cuenta').click(); });
    await flush();
    expect(calls.at(-1)).toEqual({ url: '/api/invitaciones/abcDEF123/confirmar', body: { correo: 'lucia@correo.pe', codigo: '123456', pin: '739104' } });
    expect(onJoined).toHaveBeenCalledWith(expect.objectContaining({ usuario: 106 }));
  });

  it('si ya tiene cuenta no le pide registrarse otra vez', async () => {
    await render({ signedIn: true });
    expect(host.textContent).toContain('Ya tienes tu cuenta');
    expect(host.querySelector('form')).toBeNull();
  });
});

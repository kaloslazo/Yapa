// @vitest-environment jsdom
import { createElement } from 'react';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { InvitePage } from './InvitePage';

// el botón de Google se reemplaza por uno que "elige" una cuenta: así se prueba el paso siguiente sin cargar nada de Google
vi.mock('./GoogleButton', () => ({
  GoogleButton: ({ onCredential }: { onCredential: (credential: string) => void }) =>
    createElement('button', { type: 'button', onClick: () => onCredential((globalThis as any).FAKE_TOKEN) }, 'Continuar con Google'), // eslint-disable-line @typescript-eslint/no-explicit-any
}));

type Call = { url: string; body: any }; // eslint-disable-line @typescript-eslint/no-explicit-any
const PREVIEW = { zona: 'Edificio Los Álamos', distrito: 'Lince', invita: 'Ana', vecinos: 3, minimo_grupo: 8 };
const b64 = (value: object) => btoa(String.fromCharCode(...new TextEncoder().encode(JSON.stringify(value)))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const tokenOf = (claims: object) => `${b64({ alg: 'RS256' })}.${b64(claims)}.firma`;

let root: Root;
let host: HTMLDivElement;
let calls: Call[];
let replies: Record<string, { status: number; body: unknown }>;

const setValue = (input: HTMLInputElement, value: string) => {
  if (input.type === 'checkbox') { input.click(); return; }
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(input, value);
  input.dispatchEvent(new Event('input', { bubbles: true }));
};
const field = (label: string) => [...host.querySelectorAll('label.auth-field')].find((l) => l.textContent?.includes(label))!.querySelector('input')!;
const button = (text: string) => [...host.querySelectorAll('button')].find((b) => b.textContent?.includes(text))!;
const flush = () => act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)); });
const consent = () => host.querySelector('input[type=checkbox]') as HTMLInputElement;

async function render(props: Partial<Parameters<typeof InvitePage>[0]> = {}) {
  const onJoined = vi.fn();
  await act(async () => { root.render(createElement(InvitePage, { code: 'abcDEF123', googleClientId: 'cliente.apps.googleusercontent.com', signedIn: false, onJoined, onGoHome: vi.fn(), ...props })); });
  await flush();
  return onJoined;
}

beforeEach(() => {
  (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
  (globalThis as any).FAKE_TOKEN = tokenOf({ name: 'Raith Bravo', email: 'raith@gmail.com' }); // eslint-disable-line @typescript-eslint/no-explicit-any
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
  it('muestra quién invita y la zona, y primero deja elegir cómo registrarse', async () => {
    await render();
    expect(host.textContent).toContain('Ana te invita');
    expect(host.textContent).toContain('Edificio Los Álamos · Lince');
    expect(host.textContent).toContain('3 vecinos');
    expect(button('Continuar con Google')).toBeTruthy();
    expect(button('Registrarme con mi correo')).toBeTruthy();
    expect(host.querySelector('input')).toBeNull(); // todavía ningún campo
  });

  it('un enlace que no vale lo dice claro', async () => {
    replies = {};
    await render();
    expect(host.textContent).toContain('Este enlace no sirve');
  });

  it('con Google: muestra el nombre y el correo ya llenos y de solo lectura, y pide solo celular y aceptación', async () => {
    replies['/api/invitaciones/abcDEF123/google'] = { status: 200, body: { usuario: 107, nombre: 'Raith Bravo', rol: 'vecino', csrf: 't' } };
    const onJoined = await render();
    await act(async () => { button('Continuar con Google').click(); });
    expect(field('nombre').value).toBe('Raith Bravo');
    expect(field('correo').value).toBe('raith@gmail.com');
    expect(field('nombre').readOnly).toBe(true);
    expect(field('correo').readOnly).toBe(true);
    await act(async () => { button('Crear mi cuenta').click(); });
    expect(host.textContent).toContain('9 dígitos');
    expect(calls.filter((c) => c.url.endsWith('/google'))).toHaveLength(0);
    await act(async () => { setValue(field('celular'), '995593228'); });
    expect(host.textContent).not.toContain('9 dígitos'); // al escribir se quita el aviso viejo
    await act(async () => { button('Crear mi cuenta').click(); });
    expect(host.textContent).toContain('aceptar');
    await act(async () => { consent().click(); });
    await act(async () => { button('Crear mi cuenta').click(); });
    await flush();
    expect(calls.at(-1)).toEqual({ url: '/api/invitaciones/abcDEF123/google', body: { credential: (globalThis as any).FAKE_TOKEN, celular: '995593228', consentimiento: true } }); // eslint-disable-line @typescript-eslint/no-explicit-any
    expect(onJoined).toHaveBeenCalledWith(expect.objectContaining({ usuario: 107 }));
  });

  it('si Google no trae un token legible, avisa y no avanza', async () => {
    (globalThis as any).FAKE_TOKEN = 'no-es-un-token'; // eslint-disable-line @typescript-eslint/no-explicit-any
    await render();
    await act(async () => { button('Continuar con Google').click(); });
    expect(host.textContent).toContain('No pudimos leer tu cuenta de Google');
    expect(host.querySelector('input')).toBeNull();
  });

  it('se puede cambiar de cuenta de Google', async () => {
    await render();
    await act(async () => { button('Continuar con Google').click(); });
    await act(async () => { button('Usar otra cuenta de Google').click(); });
    expect(button('Continuar con Google')).toBeTruthy();
  });

  it('sin Client ID de Google solo ofrece el correo', async () => {
    await render({ googleClientId: null });
    expect(host.textContent).not.toContain('Continuar con Google');
    expect(button('Registrarme con mi correo')).toBeTruthy();
  });

  it('con correo: valida, pide el código y luego crea la cuenta con el PIN elegido', async () => {
    replies['/api/invitaciones/abcDEF123/correo'] = { status: 200, body: { enviado: true } };
    replies['/api/invitaciones/abcDEF123/confirmar'] = { status: 200, body: { usuario: 106, nombre: 'Lucía Ramos', rol: 'vecino', csrf: 't' } };
    const onJoined = await render();
    await act(async () => { button('Registrarme con mi correo').click(); });
    await act(async () => { button('Enviarme el código').click(); });
    expect(host.textContent).toContain('Escribe tu nombre');
    expect(calls.filter((c) => c.url.endsWith('/correo'))).toHaveLength(0);
    await act(async () => {
      setValue(field('nombre'), 'Lucía Ramos');
      setValue(field('correo'), 'lucia@correo.pe');
      setValue(field('celular'), '987654321');
      consent().click();
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

  it('el consentimiento enlaza a la privacidad en otra pestaña, y el título dice quién invita (PU-05)', async () => {
    await render();
    await act(async () => { button('Registrarme con mi correo').click(); });
    const link = host.querySelector('.invite-consent a') as HTMLAnchorElement;
    expect(link.getAttribute('href')).toBe('/privacidad');
    expect(link.target).toBe('_blank');
    expect(link.rel).toContain('noreferrer');
    expect(document.title).toBe('Ana te invita a Yapa');
  });

  it('al cambiar de paso el cursor va al primer campo que se puede escribir', async () => {
    await render();
    await act(async () => { button('Registrarme con mi correo').click(); });
    expect(document.activeElement).toBe(field('nombre'));
    (globalThis as any).FAKE_TOKEN = tokenOf({ name: 'Raith Bravo', email: 'raith@gmail.com' }); // eslint-disable-line @typescript-eslint/no-explicit-any
    await act(async () => { button('Volver').click(); });
    await act(async () => { button('Continuar con Google').click(); });
    expect(document.activeElement).toBe(field('celular')); // nombre y correo están de solo lectura
  });

  it('si ya tiene cuenta no le pide registrarse otra vez', async () => {
    await render({ signedIn: true });
    expect(host.textContent).toContain('Ya tienes tu cuenta');
    expect(host.querySelector('form')).toBeNull();
  });
});

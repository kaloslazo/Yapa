// @vitest-environment jsdom
// Iteración 78 · toda foto que va a la IA sale como JPEG con fondo blanco (BR-I, S-387).
// Spec: api/docs/desarrollo/78-fotos-con-bedrock.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { photoForAI, QUOTE_SIDE } from './photoResize';
import { SupplierListEditor } from '../components/SupplierListEditor';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

let size = { width: 480, height: 480 };
const drawn: string[] = [];
const context = {
  fillStyle: '',
  fillRect: vi.fn(() => drawn.push(`fondo ${context.fillStyle}`)),
  drawImage: vi.fn(() => drawn.push('foto')),
};
let lastCanvas: HTMLCanvasElement | null = null;

beforeEach(() => {
  drawn.length = 0;
  context.fillStyle = '';
  vi.stubGlobal('createImageBitmap', vi.fn(async () => ({ ...size, close: vi.fn() })));
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockImplementation(function (this: HTMLCanvasElement) {
    lastCanvas = this;
    return context as never;
  });
  HTMLCanvasElement.prototype.toBlob = function (done: BlobCallback, type?: string) { done(new Blob(['jpg'], { type })); };
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  vi.clearAllMocks();
});

const file = (name: string, type: string, bytes = 10) => new File([new Uint8Array(bytes)], name, { type });

describe('BR-I · foto en JPEG', () => {
  it('un PNG transparente se dibuja sobre blanco y sale JPEG', async () => {
    size = { width: 480, height: 480 };
    const out = await photoForAI(file('camote.png', 'image/png'));
    expect(out.type).toBe('image/jpeg');
    expect(drawn).toEqual(['fondo #ffffff', 'foto']);
    expect([lastCanvas!.width, lastCanvas!.height]).toEqual([480, 480]);
  });

  it('un JPEG chico va tal cual', async () => {
    size = { width: 800, height: 600 };
    const original = file('bolsa.jpg', 'image/jpeg', 100_000);
    expect(await photoForAI(original)).toBe(original);
    expect(drawn).toEqual([]);
  });

  it('una foto grande baja a 1024 px (bolsa) o 1600 px (cotización)', async () => {
    size = { width: 4000, height: 3000 };
    await photoForAI(file('bolsa.jpg', 'image/jpeg'));
    expect(lastCanvas!.width).toBe(1024);
    await photoForAI(file('lista.jpg', 'image/jpeg'), QUOTE_SIDE);
    expect(lastCanvas!.width).toBe(1600);
  });

  it('el lector de cotizaciones manda la foto ya en JPEG', async () => {
    size = { width: 480, height: 480 };
    vi.mocked(api.post).mockResolvedValue({ filas: [], nuevos: [], avisos: [], fuente: 'ia' } as never);
    const host = document.createElement('div');
    document.body.append(host);
    const root: Root = createRoot(host);
    await act(async () => root.render(createElement(SupplierListEditor, {
      initialText: 'PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,40,SUP-FRESCOS,0,3.60', busy: false, resubmit: false, onSubmit: vi.fn(),
    })));
    const input = host.querySelector<HTMLInputElement>('.quote-reader input[type=file]')!;
    Object.defineProperty(input, 'files', { configurable: true, value: [file('lista.webp', 'image/webp')] });
    await act(async () => input.dispatchEvent(new Event('change', { bubbles: true })));
    await act(async () => [...host.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent === 'Leer cotización')!.click());
    const sent = vi.mocked(api.post).mock.calls[0][1] as FormData;
    expect((sent.get('foto_archivo') as File).type).toBe('image/jpeg');
    await act(async () => root.unmount());
    host.remove();
  });
});

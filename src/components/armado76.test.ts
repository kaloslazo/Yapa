// @vitest-environment jsdom
// Iteración 76 · el detector se usa a pedido, sobre la bolsa ya registrada (AR76-G, AR76-H).
// Spec: api/docs/desarrollo/76-bolsa-con-un-toque-y-detector-a-pedido.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AdminPanel } from './AdminPanel';
import { SupplierStock } from './SupplierStock';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
vi.mock('./LazyZonesMap', () => ({ LazyZonesMap: () => null }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
const notify = vi.fn();

beforeEach(() => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {});
  Element.prototype.scrollIntoView = vi.fn();
  vi.stubGlobal('URL', Object.assign(URL, { createObjectURL: vi.fn(() => 'blob:foto'), revokeObjectURL: vi.fn() }));
});
afterEach(async () => {
  if (root) await act(async () => root.unmount());
  host?.remove();
  vi.clearAllMocks();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

async function mount(element: React.ReactNode) {
  host = document.createElement('div');
  document.body.append(host);
  root = createRoot(host);
  await act(async () => { root.render(element); });
}

const button = (text: string) => [...host.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent === text);
const posted = (path: string) => vi.mocked(api.post).mock.calls.filter((call) => call[0] === path);

async function choosePhoto(input: HTMLInputElement, name = 'bolsa.jpg') {
  const file = new File(['x'], name, { type: 'image/jpeg' });
  Object.defineProperty(input, 'files', { configurable: true, value: [file] });
  await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })); });
  return file;
}

const zone = { id: 'Z-LINCE-01', nombre: 'Edificio Los Álamos', distrito: 'Lince', contacto: 'Portería Los Álamos' };
const packing = {
  ciclo: '2026-W40', ciclos: ['2026-W40'], paradas: [{ zona: zone, entrega: null, fallida: false, en_camino: false }],
  pedidos: [{
    id: 13, ciclo: '2026-W40', zona: 'Z-LINCE-01', zona_nombre: 'Edificio Los Álamos', vecino: 'Vecino 13', estado: 'REGISTRADO',
    lineas: [{ id: 'PAPA-AMARILLA', nombre: 'Papa amarilla', cantidad: '5', unidad: 'kg' }, { id: 'AJO', nombre: 'Ajo', cantidad: '1', unidad: 'kg' }],
    bolsas: [], rotulos: ['Pedido 13 · Edificio Los Álamos · Bolsa 1 de 1'],
  }],
};

describe('AR76-G · detector a pedido en el armado', () => {
  it('registra la bolsa con la foto y luego sugiere solo lo que está en el pedido', async () => {
    vi.mocked(api.get).mockImplementation(async () => packing as never);
    vi.mocked(api.post).mockImplementation(async (path: string) => (path === '/api/admin/bolsas'
      ? { pedido: 13, numero: 1, foto: 'fotos/b.jpg' }
      : path === '/api/vision/analizar'
        ? { productos: [{ producto: 'papa', cantidad: 2, confianza: 0.8 }, { producto: 'cebolla', cantidad: 3, confianza: 0.6 }] }
        : { pedido: 13, numero: 1, revision: [] }) as never);
    await mount(createElement(AdminPanel, { adminName: 'Equipo', role: 'armador' as never, notify, onLogout: vi.fn() }));

    await choosePhoto(host.querySelector<HTMLInputElement>('.pack-card input[type=file][capture]')!);
    expect(posted('/api/admin/bolsas')).toHaveLength(1);
    expect(posted('/api/vision/analizar')).toHaveLength(0);
    expect(host.querySelector('.pack-review summary')?.textContent).toBe('Revisar la foto con el detector (opcional)');

    await act(async () => button('Sugerir con el detector')!.click());
    expect(posted('/api/vision/analizar')).toHaveLength(1);
    const rows = host.querySelectorAll('.pack-review .photo-product-row');
    expect(rows).toHaveLength(1);
    expect(rows[0].querySelector('select')!.value).toBe('PAPA-AMARILLA');
    expect(host.querySelector('.pack-review')!.textContent).toContain('1 sugerencia no está en el pedido');

    await act(async () => host.querySelector<HTMLButtonElement>('.pack-review [aria-label="Confirmar producto 1"]')!.click());
    await act(async () => button('Guardar revisión de la bolsa')!.click());
    const sent = posted('/api/admin/bolsas/revision');
    expect(sent).toHaveLength(1);
    const form = sent[0][1] as FormData;
    expect(form.get('pedido')).toBe('13');
    expect(form.get('numero')).toBe('1');
    expect(JSON.parse(String(form.get('revision')))).toEqual([{ id: 'PAPA-AMARILLA', unidades: 2 }]);
  });
});

describe('AR76-H · detector a pedido en el stock del proveedor', () => {
  it('elegir la foto no llama al detector; el botón sí', async () => {
    vi.mocked(api.get).mockResolvedValue({ productos: [] } as never);
    vi.mocked(api.post).mockResolvedValue({ productos: [{ producto: 'papa', cantidad: 3 }] } as never);
    await mount(createElement(SupplierStock, {
      cycle: '2026-W40', candidates: [{ id: 'PAPA-AMARILLA', name: 'Papa amarilla', unit: 'kg' }], onApply: vi.fn(),
    }));
    await choosePhoto(host.querySelector<HTMLInputElement>('input[type=file]')!, 'carga.jpg');
    expect(posted('/api/vision/analizar')).toHaveLength(0);
    await act(async () => button('Sugerir con el detector')!.click());
    expect(posted('/api/vision/analizar')).toHaveLength(1);
    expect(host.querySelectorAll('.photo-product-row')).toHaveLength(1);
  });
});

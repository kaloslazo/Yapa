// @vitest-environment jsdom
// Iteración 66 · ver la foto que se toma (VF-A..VF-C). Spec: api/docs/desarrollo/66-ver-la-foto.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AdminPanel } from './AdminPanel';
import { OrdersPage } from './OrdersPage';
import { PhotoForm } from './PhotoForm';
import { api } from '../services/api';
import { toOrder } from '../services/mappers';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
beforeEach(() => { vi.spyOn(window, 'scrollTo').mockImplementation(() => {}); URL.createObjectURL = vi.fn(() => 'blob:vista-previa'); URL.revokeObjectURL = vi.fn(); });
afterEach(async () => { if (root) await act(async () => root.unmount()); host?.remove(); vi.clearAllMocks(); vi.restoreAllMocks(); });
async function mount(element: React.ReactNode) {
  host = document.createElement('div'); document.body.append(host); root = createRoot(host);
  await act(async () => { root.render(element); });
}
async function pick(input: HTMLInputElement) {
  Object.defineProperty(input, 'files', { value: [new File(['x'], 'foto.png', { type: 'image/png' })], configurable: true });
  await act(async () => { input.dispatchEvent(new Event('change', { bubbles: true })); });
}

describe('VF-A · vista previa al reclamar', () => {
  it('muestra la miniatura y permite cambiarla sin llamar a la API', async () => {
    const order = toOrder({ id: 12, ciclo: '2026-W40', zona: 'Z', estado: 'LIQUIDADO', pago: 'VERIFICADO', total: '10.00', lineas: [] });
    const onClaim = vi.fn();
    await mount(createElement(OrdersPage, { data: { orders: [order], balance: 0, returned: 0, supermarketSaving: 0, refunds: [] }, claimables: [{ order: 12, product: 'LIMON', name: 'Limón', quantity: 4 }], claims: [], onBack: vi.fn(), onCancel: vi.fn(), onWithdraw: vi.fn(), onClaim }));
    await pick(host.querySelector<HTMLInputElement>('.claim-form input[type=file]')!);
    expect(host.querySelector<HTMLImageElement>('.claim-form .photo-preview img')?.src).toBe('blob:vista-previa');
    expect(host.querySelector('.claim-form')?.textContent).toContain('Cambiar foto');
    expect(onClaim).not.toHaveBeenCalled();
  });
});

describe('VF-B · vista previa en las fotos del equipo', () => {
  it('el formulario de foto muestra la miniatura antes de enviar', async () => {
    const onSend = vi.fn().mockResolvedValue(true);
    await mount(createElement(PhotoForm, { label: 'Entregué', onSend }));
    await pick(host.querySelector<HTMLInputElement>('input[type=file]')!);
    expect(host.querySelector<HTMLImageElement>('.photo-preview img')?.src).toBe('blob:vista-previa');
    expect(onSend).not.toHaveBeenCalled();
  });
});

describe('VF-C · las bolsas registradas se ven en el armado', () => {
  it('una miniatura por bolsa con su enlace y su número', async () => {
    vi.mocked(api.get).mockResolvedValue({ ciclo: '2026-W40', ciclos: ['2026-W40'], paradas: [], pedidos: [{ id: 12, ciclo: '2026-W40', zona: 'Z', zona_nombre: 'Edificio Los Álamos', vecino: 'Carmen', lineas: [], bolsas: [{ numero: 1, foto: 'fotos/aa.png' }, { numero: 2, foto: 'fotos/bb.png' }] }] } as never);
    await mount(createElement(AdminPanel, { adminName: 'Armado', role: 'armador', notify: vi.fn(), onLogout: vi.fn() }));
    const bags = host.querySelectorAll<HTMLAnchorElement>('.pack-bags a');
    expect(bags).toHaveLength(2);
    expect(bags[0].getAttribute('href')).toBe('/api/admin/foto?ruta=fotos%2Faa.png');
    expect(bags[1].textContent).toContain('Bolsa 2');
  });
});

// @vitest-environment jsdom
// Iteración 67 · cantidades con su unidad (UN-D). Spec: api/docs/desarrollo/67-cantidades-con-unidad.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AdminPanel } from './AdminPanel';
import { OrdersPage } from './OrdersPage';
import { api } from '../services/api';
import { toOrder } from '../services/mappers';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
beforeEach(() => { vi.spyOn(window, 'scrollTo').mockImplementation(() => {}); });
afterEach(async () => { if (root) await act(async () => root.unmount()); host?.remove(); vi.clearAllMocks(); vi.restoreAllMocks(); });
async function mount(element: React.ReactNode) {
  host = document.createElement('div'); document.body.append(host); root = createRoot(host);
  await act(async () => { root.render(element); });
}
const lines = [{ id: 'PAPA-AMARILLA', nombre: 'Papa amarilla', cantidad: '5', unidad: 'kg', precio_max: '4.03', total: '20.15' }, { id: 'LIMPIATODO-GALON', nombre: 'Limpiatodo galón 3.8 L', cantidad: '2', unidad: 'unidad', precio_max: '7.90', total: '15.80' }];

describe('UN-D · las cantidades llevan su unidad', () => {
  it('en la tarjeta de armado', async () => {
    vi.mocked(api.get).mockResolvedValue({ ciclo: '2026-W40', ciclos: ['2026-W40'], paradas: [], pedidos: [{ id: 12, ciclo: '2026-W40', zona: 'Z', vecino: 'Carmen', lineas: lines, bolsas: [] }] } as never);
    await mount(createElement(AdminPanel, { adminName: 'Armado', role: 'armador', notify: vi.fn(), onLogout: vi.fn() }));
    const text = host.querySelector('.pack-lines')?.textContent ?? '';
    expect(text).toContain('5 kg');
    expect(text).toContain('2 unidades');
  });
  it('en el carrito del pedido y al reclamar', async () => {
    const order = toOrder({ id: 12, ciclo: '2026-W40', zona: 'Z', estado: 'LIQUIDADO', pago: 'VERIFICADO', total: '35.95', lineas: lines });
    await mount(createElement(OrdersPage, { data: { orders: [order], balance: 0, returned: 0, supermarketSaving: 0, refunds: [] }, claimables: [{ order: 12, product: 'PAPA-AMARILLA', name: 'Papa amarilla', quantity: 5, unit: 'kg' }], claims: [], onBack: vi.fn(), onCancel: vi.fn(), onWithdraw: vi.fn(), onClaim: vi.fn() }));
    expect(host.querySelector('.order-cart')?.textContent).toContain('5 kg');
    expect(host.querySelector('.claim-pick')?.textContent).toContain('5 kg');
  });
});

// @vitest-environment jsdom
// Iteración 68 · Predicción de demanda (PD-K). Spec: api/docs/desarrollo/68-prediccion-de-demanda.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AdminPanel } from './AdminPanel';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
vi.mock('./LazyZonesMap', () => ({ LazyZonesMap: () => null }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
beforeEach(() => { vi.spyOn(window, 'scrollTo').mockImplementation(() => {}); });
afterEach(async () => { if (root) await act(async () => root.unmount()); host?.remove(); vi.clearAllMocks(); vi.restoreAllMocks(); });

const product = (id: string, nombre: string, estimado: string, pedido: string, supera = false) => ({
  id, nombre, unidad: 'kg', historia: ['0', '0', '0', '0', '10', '12', '14', '21'], estimado, pedido, maximo: '20', supera_maximo: supera, metodo: 'tendencia',
});
const purchases = (parcial: boolean, error: string | null) => ({
  ciclo: '2026-W40', ciclos: ['2026-W40'], proveedores: [], parcial, colchon: { valor: '0', tope: '300', stock: [] },
  compra_real: null, flete: null, guardables: [],
  prediccion: { ciclo: '2026-W40', productos: [product('PAPA-AMARILLA', 'Papa amarilla', '23', '9', true), product('CEBOLLA-ROJA', 'Cebolla roja', '6', '2'), product('LIMON', 'Limón', '0', '0')], zonas: [], error_medio: error },
});
async function mount(data: unknown) {
  vi.mocked(api.get).mockImplementation(async () => data as never);
  host = document.createElement('div'); document.body.append(host); root = createRoot(host);
  await act(async () => { root.render(createElement(AdminPanel, { adminName: 'Compras', role: 'compras', notify: vi.fn(), onLogout: vi.fn() })); });
}

describe('PD-K · lo que se viene en Compra de la semana', () => {
  it('muestra el estimado, lo ya pedido y el aviso cuando supera el máximo', async () => {
    await mount(purchases(true, null));
    const card = host.querySelector('.forecast-card')!;
    expect(host.textContent).toContain('Lo que se viene esta semana');
    const rows = [...card.querySelectorAll('.forecast-row')];
    expect(rows).toHaveLength(2); // sin estimado ni pedido no se muestra
    expect(rows[0].textContent).toContain('23 kg');
    expect(rows[0].textContent).toContain('9 kg');
    expect(rows[0].textContent).toContain('Pide más al mayorista');
    expect(rows[1].textContent).not.toContain('Pide más al mayorista');
  });
  it('con la semana cerrada muestra cuánto se equivocó', async () => {
    await mount(purchases(false, '0.15'));
    expect(host.querySelector('.forecast-card')!.textContent).toContain('15 %');
  });
});

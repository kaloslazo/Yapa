// @vitest-environment jsdom
// Iteración 64 · la operación en el celular (OC-E..OC-H). Spec: api/docs/desarrollo/64-operacion-en-el-celular.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AdminPanel } from './AdminPanel';
import { PartnerPanel } from './PartnerPanel';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
vi.mock('./LazyZonesMap', () => ({ LazyZonesMap: () => null }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
const notify = vi.fn();
beforeEach(() => { vi.spyOn(window, 'scrollTo').mockImplementation(() => {}); Element.prototype.scrollIntoView = vi.fn(); }); // jsdom no trae scrollIntoView
afterEach(async () => { if (root) await act(async () => root.unmount()); host?.remove(); vi.clearAllMocks(); vi.restoreAllMocks(); });
async function mount(element: React.ReactNode) {
  host = document.createElement('div'); document.body.append(host); root = createRoot(host);
  await act(async () => { root.render(element); });
}
const panel = (role: string) => createElement(AdminPanel, { adminName: 'Equipo', role: role as never, notify, onLogout: vi.fn() });
const zone = { id: 'Z-LINCE-01', nombre: 'Edificio Los Álamos', distrito: 'Lince', contacto: 'Portería Los Álamos' };
const line = (id: string, nombre: string, cantidad: string) => ({ id, nombre, cantidad, precio_max: '2.00', total: '10.00' });
const order = (id: number, bolsas: number) => ({
  id, ciclo: '2026-W40', zona: 'Z-LINCE-01', zona_nombre: 'Edificio Los Álamos', vecino: `Vecino ${id}`, estado: 'REGISTRADO', pago: 'VERIFICADO',
  total: '61.00', lineas: [line('PAPA-AMARILLA', 'Papa amarilla', '5'), line('CEBOLLA-ROJA', 'Cebolla roja', '10')],
  bolsas: Array.from({ length: bolsas }, (_, i) => ({ numero: i + 1, foto: 'fotos/b.png' })), rotulos: [`Pedido ${id} · Edificio Los Álamos · Bolsa 1 de 1`],
});
const packing = { ciclo: '2026-W40', ciclos: ['2026-W40'], paradas: [{ zona: zone, entrega: null, fallida: false, en_camino: false }], pedidos: [order(12, 1), order(13, 0), order(14, 0)] };
const purchases = {
  ciclo: '2026-W40', ciclos: ['2026-W40'], parcial: false, flete: null,
  proveedores: [{ id: 'SUP-FRESCOS', nombre: 'Proveedor aliado de frescos', total: '362.40', lineas: [{ producto: 'PAPA-AMARILLA', nombre: 'Papa amarilla', cantidad: '38', unidad: 'kg', desde: '0', precio: '3.60', monto: '136.80' }] }],
  compra_real: { recibido: {}, faltantes: [{ pedido: 12, producto: 'PAPA-AMARILLA', nombre: 'Papa amarilla', cantidad: '2', colchon: '0', origen: 'COMPRA' }] },
  colchon: { valor: '0.00', tope: '500.00', stock: [] },
  guardables: [{ id: 'LIMPIATODO-GALON', nombre: 'Limpiatodo galón 3.8 L', unidad: 'unidad' }, { id: 'LEJIA-GALON', nombre: 'Lejía galón', unidad: 'unidad' }],
};
const visible = () => (host.textContent ?? '') + [...host.querySelectorAll('input')].map((e) => e.value).join(' ') + [...host.querySelectorAll('select')].map((s) => s.selectedOptions[0]?.textContent ?? '').join(' ');

describe('OC-E · las tablas se leen como tarjetas en el celular', () => {
  it('cada celda lleva el nombre de su columna', async () => {
    vi.mocked(api.get).mockImplementation(async (path: string) => (path.startsWith('/api/admin/resumen')
      ? { ciclo: '2026-W40', ciclos: ['2026-W40'], abierto: true, liquidado: false, indicadores: { pedidos: 1, por_verificar: 0, verificado: '61.00', vecinos: 1 }, grupos: [], por_verificar: [], pedidos: [order(12, 0)] }
      : { reclamos: [], devoluciones: [], propuestas: [], solicitudes: [] }) as never);
    await mount(panel('admin'));
    const cells = [...host.querySelectorAll('.admin-table tbody td')];
    expect(cells.length).toBeGreaterThan(0);
    expect(cells.every((td) => td.getAttribute('data-label'))).toBe(true);
    expect(cells[0].getAttribute('data-label')).toBe('Pedido');
  });
});

describe('OC-F · elegir en vez de escribir', () => {
  it('el colchón se llena eligiendo un producto de limpieza por su nombre', async () => {
    vi.mocked(api.get).mockImplementation(async () => purchases as never);
    vi.mocked(api.post).mockResolvedValue({} as never);
    await mount(panel('compras'));
    const form = [...host.querySelectorAll('form')].find((f) => f.textContent?.includes('Guardar en el colchón'))!;
    expect(form.querySelector('input[placeholder="LIMPIATODO-GALON"]')).toBeNull();
    const select = form.querySelector('select')!;
    expect([...select.options].map((o) => o.textContent)).toEqual(['Limpiatodo galón 3.8 L', 'Lejía galón']);
    expect(visible()).not.toContain('Código del producto');
  });
  it('la incidencia se registra eligiendo el pedido de una lista', async () => {
    vi.mocked(api.get).mockImplementation(async (path: string) => (path.startsWith('/api/admin/pedidos')
      ? { ciclo: '2026-W40', ciclos: ['2026-W40'], pedidos: [{ id: 12, vecino: 'Carmen Díaz', zona: 'Edificio Los Álamos', estado: 'LIQUIDADO' }, { id: 13, vecino: 'Lucía Ramos', zona: 'Edificio Los Álamos', estado: 'LIQUIDADO' }] }
      : { reclamos: [], devoluciones: [], solicitudes: [], incidencias: [] }) as never);
    vi.mocked(api.post).mockResolvedValue({} as never);
    await mount(panel('atencion'));
    const tab = [...host.querySelectorAll('.admin-nav-link')].find((b) => b.textContent?.includes('Incidencias')) as HTMLButtonElement;
    await act(async () => tab.click());
    const form = [...host.querySelectorAll('form')].find((f) => f.textContent?.includes('Qué pasó'))!;
    expect(form.querySelector('input[inputmode="numeric"]')).toBeNull();
    const choice = [...form.querySelectorAll('select option')].map((o) => o.textContent);
    expect(choice).toContain('Pedido 13 · Lucía Ramos · Edificio Los Álamos');
  });
});

describe('OC-G · armado con la cámara', () => {
  it('una tarjeta por pedido, el avance y la bolsa se registra al elegir la foto', async () => {
    vi.mocked(api.get).mockImplementation(async () => packing as never);
    vi.mocked(api.post).mockResolvedValue({} as never);
    await mount(panel('armador'));
    expect(host.querySelectorAll('.pack-card')).toHaveLength(3);
    expect(visible()).toContain('1 de 3 pedidos con bolsa');
    expect(host.querySelector('.pack-card')?.textContent).toContain('Papa amarilla');
    // La tarjeta también ofrece fotos pendientes con confirmación; aquí probamos la cámara directa.
    const camera = host.querySelectorAll<HTMLInputElement>('.pack-camera input[type=file]')[1];
    const file = new File(['x'], 'bolsa.png', { type: 'image/png' });
    Object.defineProperty(camera, 'files', { value: [file] });
    await act(async () => { camera.dispatchEvent(new Event('change', { bubbles: true })); });
    expect(api.post).toHaveBeenCalledWith('/api/admin/bolsas', expect.any(FormData));
    const sent = vi.mocked(api.post).mock.calls[0][1] as FormData;
    expect(sent.get('pedido')).toBe('13');
    expect(sent.get('foto_archivo')).toBe(file);
  });
});

describe('OC-H · sin claves internas a la vista', () => {
  it('armado, compras y devoluciones muestran nombres', async () => {
    vi.mocked(api.get).mockImplementation(async () => packing as never);
    await mount(panel('armador'));
    expect(visible()).not.toContain('Z-LINCE-01');
    expect(visible()).toContain('Edificio Los Álamos');
    await act(async () => root.unmount());
    vi.mocked(api.get).mockImplementation(async () => purchases as never);
    root = createRoot(host);
    await act(async () => { root.render(panel('compras')); });
    expect(visible()).not.toContain('SUP-FRESCOS');
    expect(visible()).not.toContain('2026-W40');
    await act(async () => root.unmount());
    vi.mocked(api.get).mockImplementation(async () => ({ reclamos: [], solicitudes: [], incidencias: [], devoluciones: [{ id: 3, vecino: 'Ana Torres', monto: '5.00', motivo: 'SOLICITUD_CLIENTE', vence: '2026-11-02' }] }) as never);
    root = createRoot(host);
    await act(async () => { root.render(panel('atencion')); });
    const tab = [...host.querySelectorAll('.admin-nav-link')].find((b) => b.textContent?.includes('Devoluciones')) as HTMLButtonElement;
    await act(async () => tab.click());
    expect(visible()).not.toContain('SOLICITUD_CLIENTE');
    expect(visible()).toContain('Pidió su saldo');
  });
  it('la portería ve su edificio sin la clave de la zona', async () => {
    vi.mocked(api.get).mockImplementation(async () => ({ ciclo: '2026-W40', ciclos: ['2026-W40'], zona: zone, estado: 'pendiente', seguimiento: 'preparando', pedidos: [], hitos: [] }) as never);
    await mount(createElement(PartnerPanel, { account: { user: 'p', name: 'Portería', role: 'porteria', csrf: '' } as never, notify, onLogout: vi.fn() }));
    expect(visible()).toContain('Edificio Los Álamos');
    expect(visible()).not.toContain('Z-LINCE-01');
  });
});

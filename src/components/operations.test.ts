// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AdminPanel } from './AdminPanel';
import { SupplierListEditor } from './SupplierListEditor';
import { PartnerPanel } from './PartnerPanel';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));
vi.mock('./LazyZonesMap', () => ({ LazyZonesMap: () => null }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
const notify = vi.fn();
beforeEach(() => { vi.spyOn(window, 'scrollTo').mockImplementation(() => {}); });
async function mount(element: React.ReactNode) {
  host = document.createElement('div'); document.body.append(host); root = createRoot(host);
  await act(async () => { root.render(element); });
}
async function choose(select: HTMLSelectElement, value: string) {
  await act(async () => { select.value = value; select.dispatchEvent(new Event('change', { bubbles: true })); });
}
afterEach(async () => { if (root) await act(async () => root.unmount()); host?.remove(); vi.clearAllMocks(); vi.restoreAllMocks(); vi.useRealTimers(); });
const zone = (id: string) => ({ id, nombre: id, distrito: 'Lince' });

describe('PA-02 y AT-01 · operación por zona y completados', () => {
  it('filtra entregas y bolsas juntas y conserva la semana ISO al consultar', async () => {
    vi.mocked(api.get).mockImplementation(async () => ({ ciclo: '2026-W39', ciclos: ['2026-W39', '2026-W40'], paradas: ['Z-LINCE-01', 'Z-JM-01'].map(id => ({ zona: zone(id) })), pedidos: ['Z-LINCE-01', 'Z-JM-01'].map((id, i) => ({ id: i + 1, zona: id, vecino: `Persona ${i + 1}`, lineas: [], bolsas: [] })) }) as never);
    await mount(createElement(AdminPanel, { adminName: 'Armado', role: 'armador', notify, onLogout: vi.fn() }));
    expect(host.textContent).toContain('Antes de esa hora, la semana todavía recibe compras.');
    expect(host.textContent).toContain('miércoles a las 8 p. m. (hora de Lima)');
    expect(host.querySelectorAll('.pack-multiple-bags')).toHaveLength(2);
    expect(host.textContent).toContain('Entregas por zona (2)');
    expect(host.querySelector('option')?.textContent).toBe('21 sep – 27 sep 2026');
    const filter = [...host.querySelectorAll('select')].find(s => [...s.options].some(o => o.textContent === 'Todas las zonas'))!;
    await choose(filter, 'Z-LINCE-01');
    expect(host.textContent).toContain('Entregas por zona (1)');
    expect(host.querySelectorAll('.stop-card')).toHaveLength(1);
    expect(host.querySelectorAll('.pack-card')).toHaveLength(1); // iteración 64: el armado son tarjetas (S-331)
    expect(host.querySelector('.pack-list')?.textContent).toContain('Persona 1');
    await choose(host.querySelector('select')!, '2026-W40');
    expect(api.get).toHaveBeenCalledWith('/api/admin/armado?ciclo=2026-W40');
    expect(filter.value).toBe('');
  });
  it('muestra Completados vacío y luego aprobados y rechazados con su resultado', async () => {
    const claims: Array<Record<string, unknown>> = [];
    vi.mocked(api.get).mockImplementation(async () => ({ reclamos: claims, devoluciones: [], solicitudes: [] }) as never);
    await mount(createElement(AdminPanel, { adminName: 'Atención', role: 'atencion', notify, onLogout: vi.fn() }));
    expect(host.textContent).toContain('Completados (0)');
    expect(host.textContent).toContain('Todavía no hay reclamos completados');
    await act(async () => root.unmount());
    claims.push({ id: 1, estado: 'APROBADO', vecino: 'Ana', producto: 'Papa', cantidad: 1, devuelto: '3.50' }, { id: 2, estado: 'RECHAZADO', vecino: 'Carmen', producto: 'Ajo', cantidad: 1, devuelto: '0' });
    root = createRoot(host);
    await act(async () => { root.render(createElement(AdminPanel, { adminName: 'Atención', role: 'atencion', notify, onLogout: vi.fn() })); });
    expect(host.textContent).toContain('Completados (2)');
    expect(host.textContent).toContain('Aprobado'); expect(host.textContent).toContain('Rechazado');
    expect(host.querySelectorAll('tbody button')).toHaveLength(0);
  });
});

describe('PV-02 · propuesta con campos', () => {
  it('añade un producto y bloquea enviar la fila incompleta; envía intactos los tramos válidos', async () => {
    const list = 'AJO,Ajo,FRESCOS,kg,0.25,40,SUP-FRESCOS,0,4.80,20,4.40';
    const submit = vi.fn().mockResolvedValue(true);
    await mount(createElement(SupplierListEditor, { initialText: list, busy: false, onSubmit: submit, resubmit: false }));
    await act(async () => { host.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
    expect(submit.mock.calls[0][0]).toContain('0,4.80,20,4.40');
    const add = [...host.querySelectorAll('button')].find(b => b.textContent === 'Añadir producto')!;
    await act(async () => add.click());
    expect(host.querySelectorAll('.supplier-product')).toHaveLength(2);
    await act(async () => { host.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); });
    expect(submit).toHaveBeenCalledTimes(1);
    expect(host.querySelector('[role="alert"]')?.textContent).toContain('completa código y nombre');
  });
});

describe('PO-02 · actualización automática de portería', () => {
  it('notifica hitos nuevos, no repite al actualizar y cancela el intervalo al salir', async () => {
    vi.useFakeTimers();
    const data = { ciclo: '2026-W39', ciclos: ['2026-W39'], zona: zone('Z-LINCE-01'), estado: 'pendiente', seguimiento: 'listo', pedidos: [], hitos: [] as Array<{ estado: string; hora: string }> };
    vi.mocked(api.get).mockImplementation(async () => structuredClone(data) as never);
    await mount(createElement(PartnerPanel, { account: { user: 'p', name: 'Portería', role: 'porteria', csrf: '' }, notify, onLogout: vi.fn() }));
    expect(notify).not.toHaveBeenCalled();
    data.seguimiento = 'entregada'; data.hitos.push({ estado: 'en_camino', hora: '2026-09-26T10:00:00-05:00' }, { estado: 'entregada', hora: '2026-09-26T11:00:00-05:00' });
    await act(async () => { await vi.advanceTimersByTimeAsync(15_000); });
    expect(notify).toHaveBeenCalledWith(expect.stringContaining('En camino'), 'success');
    expect(notify).toHaveBeenCalledTimes(1);
    await act(async () => { await vi.advanceTimersByTimeAsync(6_000); });
    expect(notify).toHaveBeenCalledWith(expect.stringContaining('Llegó al edificio'), 'success');
    await act(async () => { await vi.advanceTimersByTimeAsync(15_000); });
    expect(notify).toHaveBeenCalledTimes(2);
    await act(async () => root.unmount());
    expect(vi.getTimerCount()).toBe(0);
  });
});

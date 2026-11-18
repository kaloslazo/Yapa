// @vitest-environment jsdom
// Iteración 74 · recorrido por calles. Spec: api/docs/desarrollo/74-ruta-por-calles.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, expect, it, vi } from 'vitest';
import { RoutePlanner } from './RoutePlanner';
import { api } from '../services/api';

vi.mock('../services/api', () => ({ api: { post: vi.fn() } }));
// el mapa real no corre en jsdom: el doble anota cuántos puntos de calle recibió
vi.mock('./LazyRouteMap', () => ({
  LazyRouteMap: ({ geometry }: { geometry?: number[][] }) => createElement('div', { 'data-road': geometry?.length ?? 0 }),
}));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

let host: HTMLDivElement;
let root: Root;
afterEach(async () => {
  await act(async () => root.unmount());
  host.remove();
  vi.clearAllMocks();
});

const stops = [
  { zona: { id: 'A', nombre: 'A', lat: -12, lon: -77 }, estado: 'pendiente', pedidos: [{ id: 1, bolsas: 1 }] },
  { zona: { id: 'B', nombre: 'B', lat: -12.01, lon: -77.01 }, estado: 'pendiente', pedidos: [{ id: 2, bolsas: 1 }] },
];

async function mount() {
  host = document.createElement('div');
  document.body.append(host);
  root = createRoot(host);
  await act(async () => root.render(createElement(RoutePlanner, { stops, cycle: '2026-W40', active: false, onOrder: vi.fn() })));
}

const traceButton = () => [...host.querySelectorAll<HTMLButtonElement>('button')].find((b) => b.textContent === 'Trazar por calles')!;
const roadPoints = () => host.querySelector('[data-road]')!.getAttribute('data-road');

it('RP74-E · traza solo al pedirlo y muestra la distancia vial aparte de la recta', async () => {
  vi.mocked(api.post).mockResolvedValue({ distancia_m: 2500, duracion_s: 600, coordenadas: [[-77, -12], [-77.01, -12.01]] });
  await mount();
  expect(api.post).not.toHaveBeenCalled();
  await act(async () => traceButton().click());
  expect(api.post).toHaveBeenCalledWith('/api/reparto/ruta', { ciclo: '2026-W40', zonas: '["A","B"]' });
  expect(host.textContent).toContain('Recorrido vial: 2.50 km');
  expect(roadPoints()).toBe('2');
});

it('RP74-F · si falla, lo dice y no dibuja una calle inventada', async () => {
  vi.mocked(api.post).mockRejectedValue(new Error('Servicio no disponible'));
  await mount();
  await act(async () => traceButton().click());
  expect(host.querySelector('[role=alert]')!.textContent).toContain('Servicio no disponible');
  expect(roadPoints()).toBe('0');
});

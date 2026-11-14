import { expect, it } from 'vitest';
import { hasCoordinates, orderDelivery, planDelivery, type RouteStop } from './deliveryRoute';
const stop = (id: string, lon: number | null, estado = 'pendiente'): RouteStop => ({ zona: { id, nombre: id, lat: -12, lon }, estado, pedidos: [{ id: 1, bolsas: 2 }] });
it('mejora el orden, mantiene el inicio y no duplica paradas', () => {
  const plan = planDelivery([stop('A', -77), stop('C', -77.02), stop('B', -77.01)]);
  expect(plan.ids).toEqual(['A', 'B', 'C']); expect(plan.proposedMeters).toBeLessThan(plan.originalMeters); expect(plan.orders).toBe(3);
});
it('conserva en camino, aparta completadas y mantiene zonas sin coordenadas', () => {
  const plan = planDelivery([stop('lista', -77, 'entregada'), stop('A', -77.02), stop('viaje', -77.01, 'en_camino'), stop('sin', null)], 'A');
  expect(plan.route[0].zona.id).toBe('viaje'); expect(plan.ids).toEqual(['viaje', 'A', 'sin', 'lista']); expect(plan.missing).toHaveLength(1);
});
it('maneja vacío, un punto, coordenadas inválidas y empate', () => {
  expect(planDelivery([]).ids).toEqual([]); expect(planDelivery([stop('A', -77)]).proposedMeters).toBe(0);
  expect(hasCoordinates(stop('A', NaN))).toBe(false); expect(hasCoordinates(stop('A', 181))).toBe(false);
  expect(planDelivery([stop('A', -77), stop('B', -77)]).ids).toEqual(['A', 'B']);
});
it('aplicar y restaurar conserva objetos y paradas recién añadidas', () => {
  const stops = [stop('B', -77), stop('A', -77.01), stop('nuevo', null)];
  expect(orderDelivery(stops, ['A', 'B']).map(s => s.zona.id)).toEqual(['A', 'B', 'nuevo']); expect(orderDelivery(stops, null)).toBe(stops);
});
it('no empeora recorridos con distintas distribuciones', () => {
  for (let seed = 0; seed < 20; seed++) {
    const stops = Array.from({ length: 9 }, (_, i) => ({ ...stop(String(i), -77 + Math.sin(i * 13 + seed) / 20), zona: { id: String(i), nombre: String(i), lat: -12 + Math.cos(i * 7 + seed) / 20, lon: -77 + Math.sin(i * 13 + seed) / 20 } }));
    const p = planDelivery(stops); expect(p.proposedMeters).toBeLessThanOrEqual(p.originalMeters + 0.01); expect(new Set(p.ids).size).toBe(stops.length);
  }
});

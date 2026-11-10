import { describe, expect, it } from 'vitest';
import { cartSubtotal, mergeSuggestion, stepDown, stepUp } from './cart';
import { homeFor, canOpenZonePanel } from './roles';
import { formatMoment } from './format';

const ajo = { step: 0.25, maxPerOrder: 10, price: 5.38 };
const papa = { step: 1, maxPerOrder: 10, price: 4.03 };

describe('FE-B · paso y tope del carrito', () => {
  it('respeta el paso del ajo y el máximo por pedido', () => {
    expect(stepUp(ajo, 0)).toBe(0.25);
    expect(stepUp(ajo, 0.25)).toBe(0.5);
    expect(stepUp(ajo, 10)).toBe(10);
    expect(stepDown(ajo, 0.25)).toBe(0);
    expect(stepUp(papa, 1)).toBe(2);
  });
});

describe('FE-E · total aproximado del carrito', () => {
  it('suma cantidad por precio máximo', () => {
    expect(cartSubtotal([
      { product: { price: 4.03 }, quantity: 5 },
      { product: { price: 1.23 }, quantity: 10 },
      { product: { price: 2.35 }, quantity: 10 },
    ])).toBeCloseTo(55.95, 2);
  });
});

describe('FE-D · a dónde va cada rol', () => {
  it('abre la pantalla de cada rol', () => {
    expect(homeFor('admin')).toBe('operaciones');
    expect(homeFor('admin_zona')).toBe('tienda');
    expect(homeFor('vecino')).toBe('tienda');
    expect(canOpenZonePanel('admin_zona')).toBe(true);
    expect(canOpenZonePanel('vecino')).toBe(false);
  });
});

// iteración 60: la canasta sugerida por la IA se suma a la canasta, sin pasar el tope de cada producto
describe('Arma mi canasta: sumar la sugerencia', () => {
  const tope = { 'PAPA-AMARILLA': 10, 'CEBOLLA-ROJA': 10 };
  it('suma a lo que ya había y respeta el tope', () => {
    expect(mergeSuggestion({ 'PAPA-AMARILLA': 8 }, [{ id: 'PAPA-AMARILLA', quantity: 4 }, { id: 'CEBOLLA-ROJA', quantity: 3 }], tope))
      .toEqual({ 'PAPA-AMARILLA': 10, 'CEBOLLA-ROJA': 3 });
  });
  it('ignora productos que ya no están en el catálogo', () => {
    expect(mergeSuggestion({}, [{ id: 'CAVIAR', quantity: 1 }], tope)).toEqual({});
  });
});

// iteración 59: hora de cada paso en hora de Lima, con día y mes de dos cifras
describe('formatMoment', () => {
  it('muestra el día, la fecha y la hora de Lima', () => {
    expect(formatMoment('2026-09-19T09:05:00-05:00')).toBe('sáb 19/09 · 09:05');
    expect(formatMoment('2026-09-16T15:00:00Z')).toBe('mié 16/09 · 10:00');
  });
});

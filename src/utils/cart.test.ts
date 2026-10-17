import { describe, expect, it } from 'vitest';
import { cartSubtotal, stepDown, stepUp } from './cart';
import { homeFor, canOpenZonePanel } from './roles';

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

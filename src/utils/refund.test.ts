import { describe, expect, it } from 'vitest';
import { minimumGap } from './cart';
import { refundPromise } from './refund';

describe('UI-A..UI-D · cuánto falta para el mínimo', () => {
  it('UI-A devuelve lo que falta', () => expect(minimumGap(32.5, 50)).toBe(17.5));
  it('UI-B es 0 al llegar al mínimo', () => expect(minimumGap(50, 50)).toBe(0));
  it('UI-C nunca es negativo', () => expect(minimumGap(80, 50)).toBe(0));
  it('UI-D redondea a centavos', () => expect(minimumGap(49.995, 50)).toBe(0.01));
});

describe('UI-E..UI-G · plazo de la devolución', () => {
  it('UI-E saldo: queda en el saldo y no vence', () => {
    const text = refundPromise('SALDO', 'YAPE');
    expect(text).toContain('saldo');
    expect(text).toContain('no vence');
  });
  it('UI-F medio de pago Yape: hasta 30 días', () => {
    const text = refundPromise('MEDIO_DE_PAGO', 'YAPE');
    expect(text).toContain('Yape');
    expect(text).toContain('30 días');
  });
  it('UI-G medio de pago Plin', () => expect(refundPromise('MEDIO_DE_PAGO', 'PLIN')).toContain('Plin'));
});

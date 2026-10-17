import { describe, expect, it } from 'vitest';
import { calculateDeliveryFee, canCheckout, createOrderCode, validateAuthInput, validateOrderSelection } from './domain';

describe('reglas comerciales de Yapa', () => {
  it('bloquea pedidos por debajo del mínimo', () => {
    expect(canCheckout(49.99)).toBe(false);
    expect(canCheckout(50)).toBe(true);
  });

  it('calcula delivery gratis desde S/ 120', () => {
    expect(calculateDeliveryFee(80)).toBe(7.9);
    expect(calculateDeliveryFee(120)).toBe(0);
  });

  it('valida el celular peruano y el correo', () => {
    expect(validateAuthInput({ mode: 'register', name: 'Andrea', phone: '987 654 321', email: 'andrea@yapa.pe', password: 'yapa1234' })).toBeNull();
    expect(validateAuthInput({ mode: 'register', name: 'Andrea', phone: '987 654', email: 'andrea@yapa.pe', password: 'yapa1234' })).toContain('9 dígitos');
    expect(validateAuthInput({ mode: 'login', email: 'no-es-correo', password: 'yapa1234' })).toContain('correo');
  });

  it('exige dirección para registrar un pedido', () => {
    const selection = { district: 'Lince', deliveryWindow: 'SAT_09_12', paymentMethod: 'BILLETERA_DIGITAL' as const, addressLine: '', reference: '', coordinates: { lat: -12.0841, lng: -77.0317 } };
    expect(validateOrderSelection(selection, 80)).toContain('dirección');
    expect(validateOrderSelection({ ...selection, addressLine: 'Av. Arequipa 1234' }, 80)).toBeNull();
  });

  it('genera códigos de pedido legibles', () => {
    expect(createOrderCode(1200)).toBe('YP-1200');
    expect(createOrderCode(9)).toBe('YP-0009');
  });
});

import { describe, expect, it } from 'vitest';
import type { OrderRecord, Product, Zone } from '../types';
import {
  balanceOf,
  canCancel,
  cancelOrder,
  createOrderCode,
  cycleId,
  isCycleOpen,
  quoteOrder,
  settleCycle,
  tierFor,
  validateAuthInput,
  validateCheckout,
} from './domain';

// los mismos precios del ciclo de demo del repo del equipo (mayorista más comisión)
function product(id: string, unit: string, tiers: Array<[number, number]>): Product {
  return {
    id, name: id, category: 'Verduras', unit, detail: '', art: 'potato', image: '', stock: 500,
    price: tiers[0][1], tiers: tiers.map(([from, price]) => ({ from, price })),
  };
}

const PAPA = product('PAPA-AMARILLA', 'kg', [[0, 4.032], [100, 3.7856], [250, 3.584]]);
const BLANCA = product('PAPA-BLANCA', 'kg', [[0, 1.232], [100, 1.0976], [250, 1.008]]);
const CEBOLLA = product('CEBOLLA-ROJA', 'kg', [[0, 2.352], [80, 2.016], [200, 1.624]]);
const LIMON = product('LIMON', 'kg', [[0, 2.352], [50, 2.128]]);
const LIMPIATODO = product('LIMPIATODO', 'unidad', [[0, 8.611], [12, 7.521]]);
const CATALOG = [PAPA, BLANCA, CEBOLLA, LIMON, LIMPIATODO];

const ZONES: Zone[] = [
  { id: 'Z-JM-01', name: 'Residencial San Felipe', district: 'Jesús María', groupId: 'G-JM', stopCost: 40, deliveryWindow: 'SAT_12_15', active: true, coordinates: { lat: 0, lng: 0 } },
  { id: 'Z-LINCE-01', name: 'Edificio Los Álamos', district: 'Lince', groupId: 'G-LINCE', stopCost: 40, deliveryWindow: 'SAT_09_12', active: true, coordinates: { lat: 0, lng: 0 } },
  { id: 'Z-LINCE-02', name: 'Condominio Las Palmeras', district: 'Lince', groupId: 'G-LINCE', stopCost: 40, deliveryWindow: 'SAT_09_12', active: true, coordinates: { lat: 0, lng: 0 } },
  { id: 'Z-LV-01', name: 'Edificio Balconcillo', district: 'La Victoria', groupId: 'G-LV', stopCost: 40, deliveryWindow: 'SAT_15_18', active: false, coordinates: { lat: 0, lng: 0 } },
];

const MONDAY = new Date('2026-09-14T10:00:00-05:00');
const WEDNESDAY_LAST_MINUTE = new Date('2026-09-16T19:59:59-05:00');
const WEDNESDAY_CLOSE = new Date('2026-09-16T20:00:00-05:00');
const CYCLE = '2026-W38';

let sequence = 0;
function order(zoneId: string, lines: Array<[Product, number]>, overrides: Partial<OrderRecord> = {}): OrderRecord {
  sequence += 1;
  const quote = quoteOrder(lines.map(([item, quantity]) => ({ product: item, quantity })));
  return {
    id: `o${sequence}`, userId: `u${sequence}`, orderCode: `YP-${sequence}`, cycleId: CYCLE, zoneId, district: '', reference: '',
    deliveryWindow: 'SAT_12_15', paymentMethod: 'YAPE', operationCode: `OP-${sequence}`, paymentStatus: 'VERIFICADO',
    maxSubtotal: quote.subtotal, deliveryCharged: quote.delivery, total: quote.total, paidExternal: quote.total, paidBalance: 0,
    status: 'REGISTRADO', itemCount: lines.length, createdAt: '', refundToBalance: 0, refundToMethod: 0,
    lines: lines.map(([item, quantity]) => ({ productId: item.id, productName: item.name, quantity, maxPrice: item.price })),
    ...overrides,
  };
}

const BASKET_A: Array<[Product, number]> = [[PAPA, 5], [BLANCA, 10], [CEBOLLA, 10]];
const BASKET_B: Array<[Product, number]> = [[PAPA, 5], [LIMON, 2], [LIMPIATODO, 4]];

describe('ciclo semanal (S-02)', () => {
  it('recibe pedidos de lunes a miércoles antes de las 20:00, hora de Lima', () => {
    expect(isCycleOpen(MONDAY)).toBe(true);
    expect(isCycleOpen(WEDNESDAY_LAST_MINUTE)).toBe(true);
    expect(isCycleOpen(WEDNESDAY_CLOSE)).toBe(false);
    expect(isCycleOpen(new Date('2026-09-19T10:00:00-05:00'))).toBe(false);
  });

  it('nombra el ciclo con la semana ISO', () => {
    expect(cycleId(MONDAY)).toBe(CYCLE);
    expect(cycleId(new Date('2026-09-14T03:00:00Z'))).toBe('2026-W37'); // domingo 22:00 en Lima
  });
});

describe('pedido con precio máximo (C-01, C-02)', () => {
  it('cobra el precio máximo más el envío máximo de S/ 5', () => {
    expect(quoteOrder(BASKET_A.map(([item, quantity]) => ({ product: item, quantity })))).toEqual({ subtotal: 56, delivery: 5, total: 61 });
  });

  it('valida en orden: zona, ciclo, pedido existente, mínimo y pago', () => {
    const base = { subtotal: 56, total: 61, zone: ZONES[0], now: MONDAY, orders: [], paymentMethod: 'YAPE', operationCode: 'OP-1', useBalance: 0 };
    expect(validateCheckout(base)).toBeNull();
    expect(validateCheckout({ ...base, zone: ZONES[3] })).toContain('zona');
    expect(validateCheckout({ ...base, now: WEDNESDAY_CLOSE })).toContain('cerrado');
    expect(validateCheckout({ ...base, subtotal: 49.99, total: 54.99 })).toContain('mínimo');
    expect(validateCheckout({ ...base, paymentMethod: 'CONTRAENTREGA' })).toContain('Yape o Plin');
    expect(validateCheckout({ ...base, operationCode: ' ' })).toContain('código');
    const previous = order('Z-JM-01', BASKET_A, { status: 'LIQUIDADO', cycleId: '2026-W37', operationCode: 'OP-1', refundToBalance: 8.94 });
    expect(validateCheckout({ ...base, orders: [previous] })).toContain('ya fue usado');
    expect(validateCheckout({ ...base, orders: [{ ...previous, cycleId: CYCLE, status: 'REGISTRADO', operationCode: 'X' }] })).toContain('Ya tienes un pedido');
  });

  it('deja pagar con saldo y no pide código si el saldo cubre todo (S-13, S-14)', () => {
    const credit = order('Z-JM-01', BASKET_A, { status: 'LIQUIDADO', cycleId: '2026-W37', refundToBalance: 70 });
    const base = { subtotal: 56, total: 61, zone: ZONES[0], now: MONDAY, orders: [credit], paymentMethod: 'YAPE', operationCode: '', useBalance: 61 };
    expect(validateCheckout(base)).toBeNull();
    expect(validateCheckout({ ...base, useBalance: 80 })).toContain('saldo');
  });
});

describe('liquidación "te devolvemos"', () => {
  it('cobra el tramo alcanzado entre todos y devuelve el ahorro como saldo', () => {
    const jm = [...Array.from({ length: 18 }, () => order('Z-JM-01', BASKET_A)), order('Z-JM-01', BASKET_B), order('Z-JM-01', BASKET_B)];
    const result = settleCycle(jm, CYCLE, ZONES, CATALOG);
    const first = result.orders.find((item) => item.orderId === jm[0].id)!;
    expect(jm[0].total).toBe(61);
    expect(first).toMatchObject({ status: 'LIQUIDADO', deliveryFinal: 2, finalTotal: 52.06, refundToBalance: 8.94 });
    const withLemon = result.orders.find((item) => item.orderId === jm[19].id)!;
    expect(jm[19].total).toBe(64.3);
    expect(withLemon).toMatchObject({ finalTotal: 60.07, refundToBalance: 4.23 });
    expect(result.products.find((item) => item.productId === 'PAPA-AMARILLA')).toMatchObject({ totalQuantity: 100, tierFrom: 100 });
    expect(tierFor(BLANCA, 180).from).toBe(100);
  });

  it('si el grupo no llega a 8 pedidos verificados, devuelve el 100 % al Yape (C-06)', () => {
    const lince = [...Array.from({ length: 5 }, () => order('Z-LINCE-01', BASKET_A)), order('Z-LINCE-02', BASKET_A), order('Z-LINCE-02', BASKET_A)];
    const result = settleCycle(lince, CYCLE, ZONES, CATALOG);
    expect(result.orders.every((item) => item.status === 'NO_ATENDIDO' && item.refundToMethod === 61)).toBe(true);
    expect(result.totalToMethod).toBe(427);
  });

  it('las zonas unidas suman para el mínimo, pero cada una paga su parada', () => {
    const lince = [...Array.from({ length: 6 }, () => order('Z-LINCE-01', BASKET_A)), order('Z-LINCE-02', BASKET_A), order('Z-LINCE-02', BASKET_A)];
    const result = settleCycle(lince, CYCLE, ZONES, CATALOG);
    expect(result.orders.every((item) => item.status === 'LIQUIDADO')).toBe(true);
    expect(result.orders.find((item) => item.orderId === lince[0].id)?.deliveryFinal).toBe(5); // 40 / 6 pasa el tope
    expect(result.orders.find((item) => item.orderId === lince[7].id)?.deliveryFinal).toBe(5);
  });

  it('un pago sin verificar no cuenta: el pedido se anula y vuelve el saldo usado', () => {
    const unverified = order('Z-JM-01', BASKET_A, { paymentStatus: 'POR_VERIFICAR', paidBalance: 10, paidExternal: 51 });
    const result = settleCycle([unverified], CYCLE, ZONES, CATALOG);
    expect(result.orders[0]).toMatchObject({ status: 'ANULADO', refundToBalance: 10, refundToMethod: 0 });
  });
});

describe('cancelación y saldo', () => {
  it('cancela antes del cierre y devuelve a donde elija el vecino', () => {
    const item = order('Z-JM-01', BASKET_A, { paidBalance: 11, paidExternal: 50 });
    expect(canCancel(item, MONDAY)).toBe(true);
    expect(canCancel(item, WEDNESDAY_CLOSE)).toBe(false);
    expect(cancelOrder(item, 'SALDO')).toEqual({ status: 'CANCELADO', refundToBalance: 61, refundToMethod: 0 });
    expect(cancelOrder(item, 'MEDIO_DE_PAGO')).toEqual({ status: 'CANCELADO', refundToBalance: 11, refundToMethod: 50 });
    expect(cancelOrder({ ...item, paymentStatus: 'POR_VERIFICAR' }, 'SALDO').refundToBalance).toBe(11); // S-20
  });

  it('el saldo suma lo devuelto y resta lo usado', () => {
    const liquidated = order('Z-JM-01', BASKET_A, { status: 'LIQUIDADO', refundToBalance: 8.94 });
    const usedBalance = order('Z-JM-01', BASKET_A, { paidBalance: 5, paidExternal: 56 });
    expect(balanceOf([liquidated, usedBalance])).toBe(3.94);
  });
});

describe('cuenta y códigos', () => {
  it('valida el celular peruano y el correo', () => {
    expect(validateAuthInput({ mode: 'register', name: 'Andrea', phone: '987 654 321', email: 'andrea@yapa.pe', password: 'yapa1234' })).toBeNull();
    expect(validateAuthInput({ mode: 'register', name: 'Andrea', phone: '987 654', email: 'andrea@yapa.pe', password: 'yapa1234' })).toContain('9 dígitos');
    expect(validateAuthInput({ mode: 'login', email: 'no-es-correo', password: 'yapa1234' })).toContain('correo');
  });

  it('genera códigos de pedido legibles', () => {
    expect(createOrderCode(1200)).toBe('YP-1200');
    expect(createOrderCode(9)).toBe('YP-0009');
  });
});

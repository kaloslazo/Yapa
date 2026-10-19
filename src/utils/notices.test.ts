import { describe, expect, it } from 'vitest';
import { badgeText, bellLabel, noticeTarget, relativeTime } from './notices';

describe('AV-13 · a dónde lleva cada aviso', () => {
  it('los de unión llevan a Mi zona', () => {
    for (const kind of ['UNION_SOLICITADA', 'UNION_ACEPTADA', 'UNION_RECHAZADA']) expect(noticeTarget(kind)).toBe('zone');
  });
  it('los de pedido y dinero llevan a Mis pedidos', () => {
    for (const kind of ['PAGO_VERIFICADO', 'LIQUIDADO', 'ENTREGADO', 'NO_ENTREGADO', 'RECLAMO_APROBADO', 'RECLAMO_RECHAZADO', 'DEVOLUCION_PAGADA']) expect(noticeTarget(kind)).toBe('orders');
  });
  it('un tipo que no conoce lleva a Mis pedidos', () => expect(noticeTarget('OTRO')).toBe('orders'));
});

describe('AV-13 · número y nombre de la campana', () => {
  it('muestra el número hasta 9 y luego 9+', () => {
    expect(badgeText(3)).toBe('3');
    expect(badgeText(9)).toBe('9');
    expect(badgeText(10)).toBe('9+');
  });
  it('el nombre accesible dice cuántos hay sin leer', () => {
    expect(bellLabel(0)).toBe('Avisos');
    expect(bellLabel(1)).toBe('Avisos: 1 sin leer');
    expect(bellLabel(4)).toBe('Avisos: 4 sin leer');
  });
});

describe('AV-13 · hora relativa', () => {
  const now = new Date('2026-09-19T10:00:00-05:00');
  it('hace segundos es ahora', () => expect(relativeTime('2026-09-19T09:59:40-05:00', now)).toBe('ahora'));
  it('hace minutos', () => expect(relativeTime('2026-09-19T09:15:00-05:00', now)).toBe('hace 45 min'));
  it('hace horas', () => expect(relativeTime('2026-09-19T07:00:00-05:00', now)).toBe('hace 3 h'));
  it('ayer', () => expect(relativeTime('2026-09-18T08:00:00-05:00', now)).toBe('ayer'));
  it('hace días', () => expect(relativeTime('2026-09-16T10:00:00-05:00', now)).toBe('hace 3 días'));
  it('pasada una semana pone la fecha', () => expect(relativeTime('2026-09-01T10:00:00-05:00', now)).toMatch(/1/));
  it('una hora que no entiende no inventa nada', () => expect(relativeTime('no es una hora', now)).toBe(''));
});

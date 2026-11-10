import { describe, expect, it } from 'vitest';
import { toAccount, toOrder } from './mappers';

const base = { usuario: 107, nombre: 'Raith Bravo', rol: 'vecino', csrf: 't', correo: 'r***@gmail.com', correo_verificado: true };

describe('cuenta del vecino', () => {
  it('sabe si ya tiene PIN (iteración 46)', () => {
    expect(toAccount({ ...base, tiene_pin: false }).hasPin).toBe(false);
    expect(toAccount({ ...base, tiene_pin: true }).hasPin).toBe(true);
  });

  it('sabe cuando el admin global está viendo como otra persona y cuando puede hacerlo (iteración 48)', () => {
    const viewing = toAccount({ ...base, rol: 'admin_zona', viendo_como: { admin: 'debug-global' } });
    expect(viewing.viewingAs).toBe('debug-global');
    expect(toAccount(base).viewingAs).toBeUndefined();
    expect(toAccount({ usuario: 'debug-global', nombre: 'Equipo Yapa', rol: 'admin', csrf: 't', puede_ver_como: true }).canViewAs).toBe(true);
    expect(toAccount({ usuario: 'admin-yapa', nombre: 'Equipo Yapa', rol: 'admin', csrf: 't', puede_ver_como: false }).canViewAs).toBe(false);
  });

  it('si el motor no lo dice, no inventa nada (el admin no tiene PIN de vecino)', () => {
    expect(toAccount({ usuario: 'admin-yapa', nombre: 'Equipo', rol: 'admin', csrf: 't' }).hasPin).toBeUndefined();
  });
});

describe('pedido en la lista de armado', () => {
  it('trae el rótulo de cada bolsa (iteración 56, S-298)', () => {
    const order = toOrder({ id: 1, ciclo: '2026-W38', zona: 'Z-JM-01', lineas: [], bolsas: [{ numero: 1, foto: 'f.jpg' }],
      rotulos: ['Pedido 1 · Residencial San Felipe · Bolsa 1 de 1'] });
    expect(order.labels).toEqual(['Pedido 1 · Residencial San Felipe · Bolsa 1 de 1']);
  });

  it('sin rótulos, no inventa ninguno', () => {
    expect(toOrder({ id: 2, lineas: [] }).labels).toBeUndefined();
  });
});

describe('seguimiento y a dónde pagar (iteración 58)', () => {
  it('trae los pasos del pedido y cuáles ya pasaron (S-309)', () => {
    const order = toOrder({ id: 3, lineas: [], seguimiento: [{ paso: 'Pedido', hecho: true }, { paso: 'Comprado', hecho: false }] });
    expect(order.tracking).toEqual([{ step: 'Pedido', done: true }, { step: 'Comprado', done: false }]);
  });

  it('trae el Plin de Yapa cuando hay que pagar (S-305)', () => {
    const order = toOrder({ id: 4, lineas: [], pagar_a: { numero: '999 000 111', titular: 'Yapa (cuenta de prueba)' } });
    expect(order.payTo).toEqual({ number: '999 000 111', holder: 'Yapa (cuenta de prueba)' });
    expect(toOrder({ id: 5, lineas: [] }).payTo).toBeUndefined();
  });
});

describe('seguimiento con horas, detalle y fotos (iteración 59)', () => {
  it('trae el estado en una frase, la hora y el detalle de cada paso, y cuántas fotos hay', () => {
    const order = toOrder({ id: 6, lineas: [],
      estado_seguimiento: { titulo: 'En camino a Residencial San Felipe', detalle: 'Salió a las 09:00.' },
      seguimiento: [{ paso: 'En camino', hecho: true, cuando: '2026-09-19T09:00:00-05:00', detalle: 'Salió hacia Residencial San Felipe' }],
      fotos: { entrega: false, bolsas: 2 } });
    expect(order.trackingStatus).toEqual({ title: 'En camino a Residencial San Felipe', detail: 'Salió a las 09:00.' });
    expect(order.tracking?.[0]).toEqual({ step: 'En camino', done: true, when: '2026-09-19T09:00:00-05:00', detail: 'Salió hacia Residencial San Felipe' });
    expect(order.photos).toEqual({ delivery: false, bags: 2 });
  });
});

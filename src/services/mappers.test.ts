import { describe, expect, it } from 'vitest';
import { toAccount } from './mappers';

const base = { usuario: 107, nombre: 'Raith Bravo', rol: 'vecino', csrf: 't', correo: 'r***@gmail.com', correo_verificado: true };

describe('cuenta del vecino', () => {
  it('sabe si ya tiene PIN (iteración 46)', () => {
    expect(toAccount({ ...base, tiene_pin: false }).hasPin).toBe(false);
    expect(toAccount({ ...base, tiene_pin: true }).hasPin).toBe(true);
  });

  it('si el motor no lo dice, no inventa nada (el admin no tiene PIN de vecino)', () => {
    expect(toAccount({ usuario: 'admin-yapa', nombre: 'Equipo', rol: 'admin', csrf: 't' }).hasPin).toBeUndefined();
  });
});

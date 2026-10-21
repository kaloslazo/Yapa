import { describe, expect, it } from 'vitest';
import { toAccount } from './mappers';

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

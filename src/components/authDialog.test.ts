import { describe, expect, it } from 'vitest';
import { LOGIN_HINT } from './AuthDialog';

describe('UX-01 · el ingreso dice con qué se entra', () => {
  it('correo, celular o número de cliente', () => {
    expect(LOGIN_HINT).toBe('Con tu correo, celular o número de cliente y tu PIN de 6 dígitos.');
  });
});

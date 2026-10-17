import { describe, expect, it } from 'vitest';
import { orderRowPermissions, profilePermissions, userRowPermissions } from './appwrite';

describe('permisos de las filas que crea el cliente', () => {
  it('solo usan el rol del propio usuario, que Appwrite sí le deja asignar', () => {
    const permissions = [...profilePermissions('u1'), ...userRowPermissions('u1'), ...orderRowPermissions('u1')];
    expect(permissions.length).toBeGreaterThan(0);
    expect(permissions.every((permission) => permission.includes('"user:u1"'))).toBe(true);
  });
});

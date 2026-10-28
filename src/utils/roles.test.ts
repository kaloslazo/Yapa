import { describe, expect, it } from 'vitest';
import { homeFor, isNeighborRole, isPartner } from './roles';

// iteración 54: reparto y proveedores no compran ni entran al panel del equipo
describe('roles', () => {
  it('reparto y proveedor tienen su propia pantalla', () => {
    expect(isPartner('transportista')).toBe(true);
    expect(isPartner('proveedor')).toBe(true);
    expect(isPartner('admin')).toBe(false);
    expect(isPartner('vecino')).toBe(false);
  });

  it('solo vecinos y admins de zona compran', () => {
    expect(isNeighborRole('vecino')).toBe(true);
    expect(isNeighborRole('admin_zona')).toBe(true);
    expect(isNeighborRole('transportista')).toBe(false);
    expect(isNeighborRole('proveedor')).toBe(false);
    expect(isNeighborRole('admin')).toBe(false);
  });

  it('el reparto no abre el centro de operaciones', () => {
    expect(homeFor('transportista')).toBe('tienda');
    expect(homeFor('admin')).toBe('operaciones');
  });
});

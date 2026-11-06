import { describe, expect, it } from 'vitest';
import { homeFor, isNeighborRole, isPartner, isStaff } from './roles';

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

// iteración 55: compras, armado y atención entran al panel del equipo; la portería tiene su pantalla
describe('personal por rol', () => {
  it('compras, armado y atención son del equipo y abren operaciones', () => {
    for (const role of ['compras', 'armador', 'atencion'] as const) {
      expect(isStaff(role)).toBe(true);
      expect(homeFor(role)).toBe('operaciones');
      expect(isPartner(role)).toBe(false);
      expect(isNeighborRole(role)).toBe(false);
    }
    expect(isStaff('admin')).toBe(true);
  });

  it('la portería tiene su propia pantalla y no compra', () => {
    expect(isPartner('porteria')).toBe(true);
    expect(isStaff('porteria')).toBe(false);
    expect(isNeighborRole('porteria')).toBe(false);
  });

  it('el reparto, el proveedor y el vecino no son del equipo', () => {
    for (const role of ['transportista', 'proveedor', 'vecino', 'admin_zona'] as const) expect(isStaff(role)).toBe(false);
  });
});

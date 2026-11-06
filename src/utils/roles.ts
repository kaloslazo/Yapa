import type { Role, StaffRole } from '../types';

export type Home = 'tienda' | 'operaciones';

// iteración 55: compras, armado y atención trabajan en el panel del equipo, cada uno con sus secciones
const STAFF: readonly Role[] = ['compras', 'armador', 'atencion'] satisfies StaffRole[];

export const ROLE_LABELS: Record<Role, string> = {
  vecino: 'Vecino',
  admin_zona: 'Admin de zona',
  admin: 'Equipo Yapa',
  compras: 'Compras',
  armador: 'Armado',
  atencion: 'Atención al cliente',
  porteria: 'Portería',
  transportista: 'Reparto',
  proveedor: 'Proveedor',
};

export function isStaff(role: Role): boolean {
  return role === 'admin' || STAFF.includes(role);
}

// FE-D: el equipo opera; el vecino y el admin de zona compran (el admin de zona además tiene su panel)
export function homeFor(role: Role): Home {
  return isStaff(role) ? 'operaciones' : 'tienda';
}

// iteraciones 54 y 55: reparto, proveedores y portería no compran ni operan; tienen su propia pantalla
export function isPartner(role: Role): boolean {
  return role === 'transportista' || role === 'proveedor' || role === 'porteria';
}

export function isNeighborRole(role: Role): boolean {
  return role === 'vecino' || role === 'admin_zona';
}

export function canOpenZonePanel(role: Role): boolean {
  return role === 'admin_zona';
}

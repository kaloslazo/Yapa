import type { Role } from '../types';

export type Home = 'tienda' | 'operaciones';

// FE-D: el admin de Yapa opera; el vecino y el admin de zona compran (el admin de zona además tiene su panel)
export function homeFor(role: Role): Home {
  return role === 'admin' ? 'operaciones' : 'tienda';
}

export function canOpenZonePanel(role: Role): boolean {
  return role === 'admin_zona';
}

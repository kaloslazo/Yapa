import type { IconName } from '../components/Icon';
import type { Role } from '../types';

export type Section = 'resumen' | 'zonas' | 'armado' | 'compras' | 'reclamos' | 'devoluciones' | 'pines' | 'conciliacion' | 'metricas' | 'catalogo' | 'referencias' | 'vecinos' | 'cuentas';

export interface SectionInfo {
  id: Section;
  label: string;
  icon: IconName;
  group: string;
  hint: string;
  roles: Role[]; // iteración 55: quién la ve; el admin ve todas menos las hechas para un rol
}

// la barra lateral agrupa las secciones por tarea; el texto corto va bajo el título de cada página
export const SECTIONS: SectionInfo[] = [
  { id: 'resumen', label: 'Resumen', icon: 'list', group: 'Semana', hint: 'Pagos por verificar, pedidos y qué grupos llegan al mínimo.', roles: ['admin'] },
  { id: 'compras', label: 'Compra de la semana', icon: 'cart', group: 'Semana', hint: 'Cuánto comprarle a cada proveedor y el colchón de reposición.', roles: ['admin', 'compras'] },
  { id: 'armado', label: 'Armado y entrega', icon: 'box', group: 'Semana', hint: 'Foto de cada bolsa y de cada entrega.', roles: ['admin', 'armador'] },
  { id: 'reclamos', label: 'Reclamos', icon: 'receipt', group: 'Atención', hint: 'Lo que faltó o llegó mal, con su foto.', roles: ['admin', 'atencion'] },
  { id: 'devoluciones', label: 'Devoluciones', icon: 'undo', group: 'Atención', hint: 'Dinero por devolver a Yape o Plin.', roles: ['admin', 'atencion'] },
  { id: 'pines', label: 'Pedidos de PIN', icon: 'key', group: 'Atención', hint: 'Vecinos que olvidaron su PIN.', roles: ['atencion'] },
  { id: 'zonas', label: 'Zonas', icon: 'map', group: 'Vecinos', hint: 'Mapa de zonas, uniones posibles y sugerencias.', roles: ['admin'] },
  { id: 'vecinos', label: 'Vecinos', icon: 'users', group: 'Vecinos', hint: 'Altas, PIN y solicitudes.', roles: ['admin'] },
  { id: 'catalogo', label: 'Catálogo', icon: 'store', group: 'Productos', hint: 'Lista de la semana con sus tramos de precio.', roles: ['admin'] },
  { id: 'referencias', label: 'Precios de referencia', icon: 'tag', group: 'Productos', hint: 'Lo que cuesta en el mercado y el supermercado.', roles: ['admin'] },
  { id: 'cuentas', label: 'Cuentas del equipo', icon: 'switch', group: 'Productos', hint: 'Cuentas de compras, armado, atención, portería, reparto y proveedores.', roles: ['admin'] },
  { id: 'conciliacion', label: 'Conciliación', icon: 'scale', group: 'Dinero', hint: 'Que lo cobrado, el saldo y lo devuelto cuadren.', roles: ['admin'] },
  { id: 'metricas', label: 'Métricas', icon: 'chart', group: 'Dinero', hint: 'Cómo va el piloto semana a semana.', roles: ['admin'] },
];

export function sectionsFor(role: Role): SectionInfo[] {
  return SECTIONS.filter((s) => s.roles.includes(role));
}

export function groupsOf(sections: SectionInfo[]): string[] {
  return [...new Set(sections.map((s) => s.group))];
}

import { formatMoney } from './format';

export function photoUrl(route: string): string {
  return route ? `/api/admin/foto?ruta=${encodeURIComponent(route)}` : '';
}

export function claimEffect(decision: 'aprobar' | 'rechazar', amount?: number): string {
  if (decision === 'rechazar') return 'no se devuelve nada';
  return amount === undefined ? 'se devuelve el valor del artículo como saldo' : `se devuelve ${formatMoney(amount)} como saldo`;
}

const plain = (text: string) => text.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

export function filterNeighbors<T extends { id: number; nombre: string; celular: string | null }>(neighbors: T[], query: string): T[] {
  const needle = plain(query.trim());
  if (!needle) return neighbors;
  return neighbors.filter((v) => plain(`${v.id} ${v.nombre} ${v.celular ?? ''}`).includes(needle));
}

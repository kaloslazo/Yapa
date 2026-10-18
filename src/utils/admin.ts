import { formatMoney } from './format';

export function photoUrl(route: string): string {
  return route ? `/api/admin/foto?ruta=${encodeURIComponent(route)}` : '';
}

export function claimEffect(decision: 'aprobar' | 'rechazar', amount?: number): string {
  if (decision === 'rechazar') return 'no se devuelve nada';
  return amount === undefined ? 'se devuelve el valor del artículo como saldo' : `se devuelve ${formatMoney(amount)} como saldo`;
}

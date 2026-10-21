// AV-13: textos y destinos de la campana de avisos

export type NoticeTarget = 'orders' | 'zone';

// los avisos de unión son del admin de zona; todo lo demás habla de un pedido o de plata
export function noticeTarget(kind: string): NoticeTarget {
  return kind.startsWith('UNION_') ? 'zone' : 'orders';
}

export function badgeText(count: number): string {
  return count > 9 ? '9+' : String(count);
}

export function bellLabel(count: number): string {
  if (count <= 0) return 'Avisos';
  return count === 1 ? 'Avisos: 1 sin leer' : `Avisos: ${count} sin leer`;
}

export function relativeTime(iso: string, now: Date): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return '';
  const minutes = Math.floor((now.getTime() - then) / 60000);
  if (minutes < 1) return 'ahora';
  if (minutes < 60) return `hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `hace ${hours} h`;
  const days = Math.floor(hours / 24);
  if (days === 1) return 'ayer';
  if (days < 7) return `hace ${days} días`;
  return new Date(iso).toLocaleDateString('es-PE', { day: 'numeric', month: 'short' });
}

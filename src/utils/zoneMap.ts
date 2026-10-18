import { formatMoney } from './format';

const PALETTE = ['#2f7d5b', '#c0452d', '#2f6fa3', '#7a4fa0', '#b7791f', '#1f8a8a'];

// cada grupo toma el siguiente color en el orden en que aparece; los ya vistos no cambian
export function groupColors(groups: string[]): Record<string, string> {
  const colors: Record<string, string> = {};
  for (const group of groups) {
    if (!(group in colors)) colors[group] = PALETTE[Object.keys(colors).length % PALETTE.length];
  }
  return colors;
}

export function drawableZones<T extends { lat: number | null; lon: number | null }>(zones: T[]): Array<T & { lat: number; lon: number }> {
  return zones.filter((z): z is T & { lat: number; lon: number } => z.lat !== null && z.lon !== null);
}

const REASONS: Record<string, string> = {
  CYCLE_CLOSED: 'Solo se unen zonas con el ciclo abierto',
  ZONES_TOO_FAR: 'Están muy lejos para compartir camión',
  LOCATION_REQUIRED: 'Falta registrar la ubicación de una zona',
};

export function unionReason(code: string): string {
  return REASONS[code] ?? 'Hoy no se pueden unir';
}

export function unionLabel(distance: number, reason: string): string {
  return `${distance} m · ${reason ? unionReason(reason) : 'se puede unir hoy'}`;
}

export function marginLabel(margin: string | null): string {
  return margin === null ? 'Sin liquidar' : formatMoney(Number(margin));
}

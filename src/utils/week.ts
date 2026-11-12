// UX-02, UX-03: fechas en palabras; Armado usa además el rango completo de la semana.

const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

const dayMonth = (date: Date) => `${date.getUTCDate()} ${MONTHS[date.getUTCMonth()]}`;

export function weekLabel(cycle: string): string {
  const match = /^(\d{4})-W(\d{2})$/.exec(cycle);
  if (!match) return cycle;
  const jan4 = new Date(Date.UTC(Number(match[1]), 0, 4)); // el 4 de enero siempre cae en la semana 1
  const monday = new Date(jan4.getTime() - ((jan4.getUTCDay() + 6) % 7) * 86_400_000 + (Number(match[2]) - 1) * 7 * 86_400_000);
  return `semana del ${dayMonth(monday)}`;
}

export function shortDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  return match ? dayMonth(new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])))) : '';
}

// Rango completo para operación; el valor del selector sigue siendo el ciclo ISO.
export function weekRangeLabel(cycle: string): string {
  const match = /^(\d{4})-W(\d{2})$/.exec(cycle);
  if (!match) return cycle;
  const jan4 = new Date(Date.UTC(Number(match[1]), 0, 4));
  const monday = new Date(jan4.getTime() - ((jan4.getUTCDay() + 6) % 7) * 86_400_000 + (Number(match[2]) - 1) * 7 * 86_400_000);
  const sunday = new Date(monday.getTime() + 6 * 86_400_000);
  const start = `${dayMonth(monday)}${monday.getUTCFullYear() !== sunday.getUTCFullYear() ? ` ${monday.getUTCFullYear()}` : ''}`;
  return `${start} – ${dayMonth(sunday)} ${sunday.getUTCFullYear()}`;
}

const currencyFormatter = new Intl.NumberFormat('es-PE', {
  style: 'currency',
  currency: 'PEN',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatMoney(value: number) {
  return currencyFormatter.format(value).replace(/\u00a0/g, ' ');
}

// iteración 59: hora de cada paso del seguimiento, en hora de Lima ("sáb 19/09 · 09:00")
export function formatMoment(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const part = (options: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat('es-PE', { timeZone: 'America/Lima', ...options }).format(date);
  const day = part({ weekday: 'short' }).replace('.', '');
  const pad = (options: Intl.DateTimeFormatOptions) => part(options).padStart(2, '0');
  return `${day} ${pad({ day: 'numeric' })}/${pad({ month: 'numeric' })} · ${pad({ hour: 'numeric', hourCycle: 'h23' })}:${pad({ minute: 'numeric' })}`;
}

// "2 unidades", "1 unidad", "3 kg": la unidad del motor viene en singular
export function quantityWithUnit(quantity: string | number, unit: string): string {
  return `${quantity} ${unit === 'unidad' && Number(quantity) !== 1 ? 'unidades' : unit}`;
}

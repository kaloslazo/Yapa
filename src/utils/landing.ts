// portada: cuenta regresiva al cierre y pizarra de precios de la semana

const LIMA_OFFSET_MS = 5 * 3_600_000; // Perú no cambia de hora: UTC−5 todo el año
const DAY_MS = 86_400_000;

// S-02: se recibe desde el lunes 00:00 hasta antes del miércoles 20:00, hora de Lima
export function closeCountdown(now: Date): { open: boolean; text: string } {
  const lima = new Date(now.getTime() - LIMA_OFFSET_MS); // sus campos UTC son la hora de Lima
  const sinceMonday = ((lima.getUTCDay() + 6) % 7) * DAY_MS + (lima.getTime() % DAY_MS);
  const left = 2 * DAY_MS + 20 * 3_600_000 - sinceMonday;
  if (left <= 0) return { open: false, text: 'Abre el lunes' };
  const days = Math.floor(left / DAY_MS);
  const hours = Math.floor((left % DAY_MS) / 3_600_000);
  const minutes = Math.floor((left % 3_600_000) / 60_000);
  return { open: true, text: days ? `Cierra en ${days} d ${hours} h` : `Cierra en ${hours} h ${minutes} min` };
}

// los productos que más ahorran frente al supermercado (solo los que tienen precio de referencia)
export function bestDeals<T extends { supermarketSaving: number | null; supermarket: unknown }>(products: T[], count: number): T[] {
  return products.filter((p) => p.supermarket && p.supermarketSaving !== null)
    .sort((a, b) => (b.supermarketSaving ?? 0) - (a.supermarketSaving ?? 0))
    .slice(0, count);
}

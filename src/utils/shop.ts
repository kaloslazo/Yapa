// tienda (fase 1 de la estructura nueva): qué mostrar en cada sección; los precios y tramos los manda el motor
import { bestDeals } from './landing';

interface Tier { from: number; price: number }
interface Shoppable { id: string; group: string; ordered: number; tiers: Tier[]; nextTier: Tier | null; supermarketSaving: number | null; supermarket: unknown }

export type Chip = 'todo' | 'ahorro' | 'por-bajar';

// cuánto se llenó el tramo siguiente entre todos (0 a 1); null si ya tiene el mejor precio
export function dropFill(product: Pick<Shoppable, 'ordered' | 'tiers' | 'nextTier'>): number | null {
  const next = product.nextTier;
  if (!next) return null;
  const reached = product.tiers.filter((t) => t.from <= product.ordered).map((t) => t.from);
  const from = reached.length ? Math.max(...reached) : 0;
  return Math.min(Math.max((product.ordered - from) / (next.from - from || 1), 0), 1);
}

// «Están por bajar»: los que ya empezaron a llenarse, del más cercano al más lejano
export function nearDrop<T extends Shoppable>(products: T[], count = Infinity): T[] {
  return products.filter((p) => p.ordered > 0 && dropFill(p) !== null)
    .sort((a, b) => (dropFill(b) ?? 0) - (dropFill(a) ?? 0))
    .slice(0, count);
}

// un grupo de la tienda; «ofertas» son los que ahorran frente al súper, del que más al que menos
export function inGroup<T extends Shoppable>(products: T[], group: string): T[] {
  return group === 'ofertas' ? bestDeals(products, products.length) : products.filter((p) => p.group === group);
}

export function applyChip<T extends Shoppable>(products: T[], chip: Chip): T[] {
  if (chip === 'ahorro') return [...products].sort((a, b) => (b.supermarketSaving ?? -1) - (a.supermarketSaving ?? -1));
  if (chip === 'por-bajar') return products.filter((p) => dropFill(p) !== null).sort((a, b) => (dropFill(b) ?? 0) - (dropFill(a) ?? 0));
  return products;
}

const LIMA_OFFSET_MS = 5 * 3_600_000;
const DAYS = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'];
const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic'];

// el sábado de entrega que viene, en hora de Lima: «sáb 14 nov»
export function deliveryDay(now: Date): string {
  const lima = new Date(now.getTime() - LIMA_OFFSET_MS);
  const ahead = (6 - lima.getUTCDay() + 7) % 7;
  const day = new Date(lima.getTime() + ahead * 86_400_000);
  return `${DAYS[day.getUTCDay()]} ${day.getUTCDate()} ${MONTHS[day.getUTCMonth()]}`;
}

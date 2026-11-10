// el carrito solo suma para mostrarlo mientras se arma (S-166); el total que vale lo da POST /api/cotizar

interface Steppable {
  step: number;
  maxPerOrder: number;
}

const round = (value: number) => Math.round(value * 100) / 100;

export function stepUp(product: Steppable, quantity: number): number {
  return Math.min(round(quantity + product.step), product.maxPerOrder || Infinity);
}

export function stepDown(product: Steppable, quantity: number): number {
  return Math.max(round(quantity - product.step), 0);
}

export function cartSubtotal(lines: Array<{ product: { price: number }; quantity: number }>): number {
  return round(lines.reduce((sum, line) => sum + line.product.price * line.quantity, 0));
}

export function formatQuantity(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/0$/, '');
}

export function minimumGap(subtotal: number, minimum: number): number {
  return Math.max(round(minimum - subtotal), 0);
}

// iteración 60: suma la canasta sugerida a la que ya hay, sin pasar el tope de cada producto del catálogo
export function mergeSuggestion(cart: Record<string, number>, lines: Array<{ id: string; quantity: number }>, maxPerOrder: Record<string, number>): Record<string, number> {
  const next = { ...cart };
  for (const { id, quantity } of lines) {
    if (!(id in maxPerOrder)) continue;
    next[id] = Math.min((next[id] ?? 0) + quantity, maxPerOrder[id]);
  }
  return next;
}

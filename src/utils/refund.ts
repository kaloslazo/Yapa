import type { RefundDestination } from '../types';

const methodName = (method: string) => (method === 'PLIN' ? 'Plin' : 'Yape');

export function refundPromise(destination: RefundDestination, method: string): string {
  if (destination === 'SALDO') return 'El dinero queda en tu saldo para tu próximo pedido y no vence.';
  return `Te lo devolvemos a tu ${methodName(method)} en hasta 30 días.`;
}

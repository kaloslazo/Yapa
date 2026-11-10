import type { Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { minimumGap } from '../utils/cart';

export const MIN_SUBTOTAL = 50; // se muestra; la regla la aplica el motor (S-04)
export const MAX_DELIVERY = 5;

export interface CartLine {
  product: Product;
  quantity: number;
}

export function minimumMessage(subtotal: number) {
  return subtotal >= MIN_SUBTOTAL ? 'Ya llegaste al pedido mínimo.' : `Te faltan ${formatMoney(minimumGap(subtotal, MIN_SUBTOTAL))} para el mínimo de ${formatMoney(MIN_SUBTOTAL)}.`;
}

export function SavingsNote({ savings }: { savings: number }) {
  if (savings <= 0) return null;
  return <p className="savings-note">Ahorras aprox. <strong>{formatMoney(savings)}</strong> frente al supermercado.</p>;
}

// la canasta flota abajo mientras compras: total, cuántos productos y la entrada a la canasta
export function CartBar({ count, subtotal, onOpenCart }: { count: number; subtotal: number; onOpenCart: () => void }) {
  const gap = minimumGap(subtotal, MIN_SUBTOTAL);
  return (
    <div className="cart-bar" role="region" aria-label="Resumen de tu canasta">
      <button className="cart-bar-summary" type="button" onClick={onOpenCart}>
        <strong>{formatMoney(subtotal)}</strong>
        <span>{count} {count === 1 ? 'producto' : 'productos'}<span className="cart-bar-gap">{gap > 0 ? ` · faltan ${formatMoney(gap)} para el mínimo` : ' · listo para pedir'}</span></span>
      </button>
      <button className="cart-bar-open" type="button" onClick={onOpenCart}><Icon name="basket" size={18} />Ver canasta</button>
    </div>
  );
}

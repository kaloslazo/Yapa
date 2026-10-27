import type { Product } from '../types';
import { Icon } from './Icon';
import { ProductVisual } from './Catalog';
import { formatMoney } from '../utils/format';
import { formatQuantity, minimumGap } from '../utils/cart';

export const MIN_SUBTOTAL = 50; // se muestra; la regla la aplica el motor (S-04)
export const MAX_DELIVERY = 5;

export interface CartLine {
  product: Product;
  quantity: number;
}

interface CartPanelProps {
  lines: CartLine[];
  subtotal: number;
  savings: number;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onCheckout: () => void;
  onFocusCatalog: () => void;
}

export function minimumMessage(subtotal: number) {
  return subtotal >= MIN_SUBTOTAL ? 'Ya llegaste al pedido mínimo.' : `Te faltan ${formatMoney(minimumGap(subtotal, MIN_SUBTOTAL))} para el mínimo de ${formatMoney(MIN_SUBTOTAL)}.`;
}

export function SavingsNote({ savings }: { savings: number }) {
  if (savings <= 0) return null;
  return <div className="savings-note"><Icon name="confetti" size={20} weight="duotone" /><span>Ahorras aprox. <strong>{formatMoney(savings)}</strong> frente al supermercado</span></div>;
}

export function CartPanel({ lines, subtotal, savings, onAdd, onDecrease, onCheckout, onFocusCatalog }: CartPanelProps) {
  const progress = Math.min((subtotal / MIN_SUBTOTAL) * 100, 100);

  return (
    <aside className="cart-panel" aria-labelledby="cart-title">
      <div className="cart-heading"><div className="cart-heading-copy"><h2 id="cart-title">Tu canasta</h2><span className="cart-count">{lines.length} {lines.length === 1 ? 'producto' : 'productos'}</span></div><span className="cart-bag" aria-hidden="true"><Icon name="basket" size={21} /></span></div>
      {lines.length ? (
        <>
          <div className="cart-lines">{lines.map(({ product, quantity }) => <div className="cart-line" key={product.id}>
            <ProductVisual product={product} className="mini-art" />
            <div className="cart-line-copy"><strong>{product.name}</strong><span>{formatMoney(product.price)} / {product.unit} · máximo</span></div>
            <div className="quantity-control" aria-label={`Cantidad de ${product.name}`}><button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={14} /></button><span>{formatQuantity(quantity)}</span><button type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={14} /></button></div>
          </div>)}</div>
          <div className="free-delivery-note"><div className="free-delivery-copy"><Icon name="check" size={17} /><span>{minimumMessage(subtotal)}</span></div><div className="progress-track"><span style={{ width: `${progress}%` }} /></div></div>
          <SavingsNote savings={savings} />
          <div className="cart-summary"><div><span>Productos a precio máximo</span><strong>{formatMoney(subtotal)}</strong></div><div><span>Envío máximo</span><strong>{formatMoney(MAX_DELIVERY)}</strong></div><div className="summary-total"><span>Pagas hoy aprox.</span><strong>{formatMoney(subtotal + MAX_DELIVERY)}</strong></div></div>
          <button className="primary-button checkout-button" type="button" onClick={onCheckout} disabled={subtotal < MIN_SUBTOTAL}>{subtotal < MIN_SUBTOTAL ? `Te faltan ${formatMoney(minimumGap(subtotal, MIN_SUBTOTAL))}` : <>Continuar pedido <Icon name="arrow" size={17} /></>}</button>
          <p className="cart-footnote">Nunca pagas más que esto. Después de la entrega te devolvemos como saldo el ahorro por volumen y lo que sobre del envío.</p>
        </>
      ) : (
        <div className="cart-empty"><div className="cart-empty-art"><Icon name="basket" size={28} /></div><h3>Tu canasta está vacía</h3><p>Agrega productos del catálogo y aquí verás el total de tu compra.</p><button className="secondary-button" type="button" onClick={onFocusCatalog}>Explorar catálogo <Icon name="arrow" size={16} /></button></div>
      )}
    </aside>
  );
}

interface MobileCartBarProps {
  count: number;
  subtotal: number;
  onCheckout: () => void;
  onOpenCart: () => void;
}

export function MobileCartBar({ count, subtotal, onCheckout, onOpenCart }: MobileCartBarProps) {
  const ready = subtotal >= MIN_SUBTOTAL;
  const progress = Math.min((subtotal / MIN_SUBTOTAL) * 100, 100);
  return (
    <div className="mobile-cart-bar" role="region" aria-label="Resumen de tu canasta">
      <button className="mobile-cart-summary" type="button" onClick={onOpenCart}>
        <span className="mobile-cart-count">{count}</span>
        <span><strong>{formatMoney(subtotal)}</strong><small>{ready ? 'Listo para pedir' : `Faltan ${formatMoney(minimumGap(subtotal, MIN_SUBTOTAL))} para el mínimo`}</small></span>
      </button>
      <button className="primary-button" type="button" onClick={ready ? onCheckout : onOpenCart}>{ready ? 'Pedir' : 'Ver canasta'} <Icon name="arrow" size={16} /></button>
      <span className="mobile-cart-progress" aria-hidden="true"><span style={{ width: `${progress}%` }} /></span>
    </div>
  );
}

import type { CartState, Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { MIN_SUBTOTAL } from '../utils/domain';

interface CartLine {
  product: Product;
  quantity: number;
}

interface CartPanelProps {
  lines: CartLine[];
  cart: CartState;
  subtotal: number;
  delivery: number;
  total: number;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onCheckout: () => void;
  onFocusCatalog: () => void;
}

export function minimumMessage(subtotal: number) {
  return subtotal >= MIN_SUBTOTAL ? 'Ya llegaste al pedido mínimo.' : `Te faltan ${formatMoney(MIN_SUBTOTAL - subtotal)} para el mínimo de ${formatMoney(MIN_SUBTOTAL)}.`;
}

export function CartPanel({ lines, subtotal, delivery, total, onAdd, onDecrease, onCheckout, onFocusCatalog }: CartPanelProps) {
  const units = lines.reduce((sum, line) => sum + line.quantity, 0);
  const progress = Math.min((subtotal / MIN_SUBTOTAL) * 100, 100);

  return (
    <aside className="cart-panel" aria-labelledby="cart-title">
      <div className="cart-heading"><div className="cart-heading-copy"><h2 id="cart-title">Tu canasta</h2><span className="cart-count">{units} {units === 1 ? 'producto' : 'productos'}</span></div><span className="cart-bag" aria-hidden="true"><Icon name="box" size={21} /></span></div>
      {lines.length ? (
        <>
          <div className="cart-lines">{lines.map(({ product, quantity }) => <div className="cart-line" key={product.id}>
            <div className={`mini-art mini-art--${product.art}`}><img className="mini-image" src={product.image} alt={product.name} width="720" height="720" /></div>
            <div className="cart-line-copy"><strong>{product.name}</strong><span>{formatMoney(product.price)} / {product.unit} · máximo</span></div>
            <div className="quantity-control" aria-label={`Cantidad de ${product.name}`}><button type="button" onClick={() => onDecrease(product)} aria-label="Quitar una unidad"><Icon name="minus" size={14} /></button><span>{quantity}</span><button type="button" onClick={() => onAdd(product)} aria-label="Agregar una unidad"><Icon name="plus" size={14} /></button></div>
          </div>)}</div>
          <div className="free-delivery-note"><div className="free-delivery-copy"><Icon name="check" size={17} /><span>{minimumMessage(subtotal)}</span></div><div className="progress-track"><span style={{ width: `${progress}%` }} /></div></div>
          <div className="cart-summary"><div><span>Productos a precio máximo</span><strong>{formatMoney(subtotal)}</strong></div><div><span>Envío máximo</span><strong>{formatMoney(delivery)}</strong></div><div className="summary-total"><span>Pagas hoy</span><strong>{formatMoney(total)}</strong></div></div>
          <button className="primary-button checkout-button" type="button" onClick={onCheckout}>Continuar pedido <Icon name="arrow" size={17} /></button>
          <p className="cart-footnote">Nunca pagas más que esto. Después de la entrega te devolvemos como saldo el ahorro por volumen y lo que sobre del envío.</p>
        </>
      ) : (
        <div className="cart-empty"><div className="cart-empty-art"><Icon name="box" size={28} /></div><h3>Tu canasta está vacía</h3><p>Agrega productos del catálogo y aquí verás el total de tu compra.</p><button className="secondary-button" type="button" onClick={onFocusCatalog}>Explorar catálogo <Icon name="arrow" size={16} /></button></div>
      )}
    </aside>
  );
}

export type { CartLine };

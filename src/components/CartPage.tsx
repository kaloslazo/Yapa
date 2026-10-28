import type { Product } from '../types';
import { Icon } from './Icon';
import { ProductVisual } from './Catalog';
import { formatMoney } from '../utils/format';
import { formatQuantity, minimumGap } from '../utils/cart';
import { MAX_DELIVERY, MIN_SUBTOTAL, minimumMessage, type CartLine } from './CartPanel';

interface CartPageProps {
  lines: CartLine[];
  subtotal: number;
  savings: number;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onCheckout: () => void;
  onBack: () => void;
}

export function CartPage({ lines, subtotal, savings, onAdd, onDecrease, onCheckout, onBack }: CartPageProps) {
  const progress = Math.min((subtotal / MIN_SUBTOTAL) * 100, 100);
  const total = subtotal + (lines.length ? MAX_DELIVERY : 0);

  return (
    <main className="customer-page" id="cart-page">
      <header className="customer-page-header">
        <div><h1>Tu canasta</h1><p>Entregamos el sábado en tu portería. Pagas el precio máximo y lo que ahorremos entre todos vuelve a tu saldo.</p></div>
      </header>

      <div className="cart-page-grid">
        <section className="customer-main-card" aria-labelledby="cart-page-title">
          <div className="customer-section-heading"><div><h2 id="cart-page-title">Productos</h2></div><span className="customer-count">{lines.length} {lines.length === 1 ? 'producto' : 'productos'}</span></div>
          {lines.length ? <><div className="cart-page-lines">{lines.map(({ product, quantity }) => <div className="cart-page-line" key={product.id}><ProductVisual product={product} className="cart-page-art" /><div className="cart-page-line-copy"><strong>{product.name}</strong><span>{product.detail}</span><small>{formatMoney(product.price)} / {product.unit}</small></div><div className="quantity-control" aria-label={`Cantidad de ${product.name}`}><button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={14} /></button><span>{formatQuantity(quantity)}</span><button type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={14} /></button></div><strong className="cart-page-line-total">{formatMoney(product.price * quantity)}</strong></div>)}</div></> : <div className="customer-empty-state"><h3>Tu canasta está vacía</h3><p>Agrega productos del catálogo para comenzar tu compra de la semana.</p><button className="primary-button" type="button" onClick={onBack}>Ver el catálogo</button></div>}
        </section>

        <aside className="cart-page-summary" aria-labelledby="cart-summary-title">
          <h2 id="cart-summary-title">Resumen</h2>
          <div className="cart-summary"><div><span>Productos a precio máximo</span><strong>{formatMoney(subtotal)}</strong></div><div><span>Envío máximo</span><strong>{formatMoney(lines.length ? MAX_DELIVERY : 0)}</strong></div>{savings > 0 ? <div className="summary-saving"><span>Ahorro frente al súper</span><strong>{formatMoney(savings)}</strong></div> : null}<div className="summary-total"><span>Pagas hoy, como máximo</span><strong>{formatMoney(total)}</strong></div></div>
          {lines.length ? <div className="minimum-note"><p className={subtotal >= MIN_SUBTOTAL ? 'is-ready' : ''}>{minimumMessage(subtotal)}</p><div className="progress-track" aria-hidden="true"><span style={{ width: `${progress}%` }} /></div></div> : null}
          <div className="cart-page-cta"><div className="cart-page-cta-total"><span>Pagas hoy</span><strong>{formatMoney(total)}</strong></div><button className="primary-button" type="button" onClick={onCheckout} disabled={subtotal < MIN_SUBTOTAL}>{lines.length && subtotal < MIN_SUBTOTAL ? `Te faltan ${formatMoney(minimumGap(subtotal, MIN_SUBTOTAL))}` : 'Continuar pedido'}</button></div>
          <p className="cart-footnote">Pagas por adelantado con Yape o Plin. Si tu zona no llega a 8 pedidos, te devolvemos el 100 %.</p>
          <button className="text-button" type="button" onClick={onBack}>Seguir comprando</button>
        </aside>
      </div>
    </main>
  );
}

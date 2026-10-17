import type { Product } from '../types';
import { Icon } from './Icon';
import { ProductVisual } from './Catalog';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';
import { MAX_DELIVERY, MIN_SUBTOTAL, minimumMessage, SavingsNote, type CartLine } from './CartPanel';

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

  return (
    <main className="customer-page" id="cart-page">
      <header className="customer-page-header">
        <div><span className="customer-eyebrow">Tu compra</span><h1>Tu canasta de la semana</h1><p>Pagas el precio máximo; lo que ahorremos entre todos vuelve como saldo después de la entrega.</p></div>
        <div className="customer-page-note"><span className="customer-page-note-icon"><Icon name="calendar" size={20} /></span><span><small>Próxima entrega</small><strong>Sábado · en tu portería</strong></span></div>
      </header>

      <div className="cart-page-grid">
        <section className="customer-main-card" aria-labelledby="cart-page-title">
          <div className="customer-section-heading"><div><span className="customer-eyebrow">Productos elegidos</span><h2 id="cart-page-title">Tu canasta</h2></div><span className="customer-count">{lines.length} {lines.length === 1 ? 'producto' : 'productos'}</span></div>
          {lines.length ? <><div className="cart-page-lines">{lines.map(({ product, quantity }) => <div className="cart-page-line" key={product.id}><ProductVisual product={product} className="cart-page-art" /><div className="cart-page-line-copy"><strong>{product.name}</strong><span>{product.detail}</span><small>{formatMoney(product.price)} / {product.unit} · máximo</small></div><div className="quantity-control" aria-label={`Cantidad de ${product.name}`}><button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={14} /></button><span>{formatQuantity(quantity)}</span><button type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={14} /></button></div><strong className="cart-page-line-total">{formatMoney(product.price * quantity)}</strong></div>)}</div><div className="cart-page-delivery"><div><Icon name="check" size={18} /><span>{minimumMessage(subtotal)}</span></div><div className="progress-track"><span style={{ width: `${progress}%` }} /></div></div></> : <div className="customer-empty-state"><span className="customer-empty-icon"><Icon name="basket" size={27} /></span><h3>Tu canasta está vacía</h3><p>Agrega productos del catálogo para comenzar tu compra de la semana.</p><button className="primary-button" type="button" onClick={onBack}>Explorar catálogo <Icon name="arrow" size={17} /></button></div>}
        </section>

        <aside className="cart-page-summary"><span className="customer-eyebrow">Resumen de compra</span><h2>Lista para el sábado</h2><SavingsNote savings={savings} /><div className="cart-page-summary-rows"><div><span>Productos a precio máximo</span><strong>{formatMoney(subtotal)}</strong></div><div><span>Envío máximo</span><strong>{formatMoney(lines.length ? MAX_DELIVERY : 0)}</strong></div><div><span>Pagas hoy aprox.</span><strong>{formatMoney(subtotal + (lines.length ? MAX_DELIVERY : 0))}</strong></div></div><button className="primary-button" type="button" onClick={onCheckout} disabled={subtotal < MIN_SUBTOTAL}>Continuar pedido <Icon name="arrow" size={17} /></button><p>Pagas por adelantado con Yape o Plin. Si tu zona no llega a 8 pedidos, te devolvemos el 100 %.</p><button className="text-button" type="button" onClick={onBack}>Agregar más productos <Icon name="arrow" size={16} /></button></aside>
      </div>
    </main>
  );
}

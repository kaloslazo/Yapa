import type { Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import type { CartLine } from './CartPanel';

interface CartPageProps {
  lines: CartLine[];
  subtotal: number;
  deliveryFee: number;
  freeDeliveryFrom: number;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onCheckout: () => void;
  onBack: () => void;
}

export function CartPage({ lines, subtotal, deliveryFee, freeDeliveryFrom, onAdd, onDecrease, onCheckout, onBack }: CartPageProps) {
  const units = lines.reduce((sum, line) => sum + line.quantity, 0);
  const total = subtotal + deliveryFee;
  const progress = Math.min((subtotal / freeDeliveryFrom) * 100, 100);
  const deliveryMessage = subtotal >= freeDeliveryFrom ? 'Tu delivery es gratis.' : `Agrega ${formatMoney(freeDeliveryFrom - subtotal)} para delivery gratis.`;

  return (
    <main className="customer-page" id="cart-page">
      <header className="customer-page-header">
        <div><span className="customer-eyebrow">Tu compra</span><h1>Tu canasta de la semana</h1><p>Revisa tus productos, confirma tu total y elige cómo recibirlos en Lima.</p></div>
        <div className="customer-page-note"><span className="customer-page-note-icon"><Icon name="calendar" size={20} /></span><span><small>Próxima entrega</small><strong>Sábado · elige tu ventana</strong></span></div>
      </header>

      <div className="cart-page-grid">
        <section className="customer-main-card" aria-labelledby="cart-page-title">
          <div className="customer-section-heading"><div><span className="customer-eyebrow">Productos elegidos</span><h2 id="cart-page-title">Tu canasta</h2></div><span className="customer-count">{units} {units === 1 ? 'producto' : 'productos'}</span></div>
          {lines.length ? <><div className="cart-page-lines">{lines.map(({ product, quantity }) => <div className="cart-page-line" key={product.id}><div className={`cart-page-art product-visual--${product.art}`}><img src={product.image} alt={product.name} width="720" height="720" /></div><div className="cart-page-line-copy"><strong>{product.name}</strong><span>{product.detail}</span><small>{formatMoney(product.price)} / {product.unit}</small></div><div className="quantity-control" aria-label={`Cantidad de ${product.name}`}><button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar una unidad de ${product.name}`}><Icon name="minus" size={14} /></button><span>{quantity}</span><button type="button" onClick={() => onAdd(product)} aria-label={`Agregar una unidad de ${product.name}`}><Icon name="plus" size={14} /></button></div><strong className="cart-page-line-total">{formatMoney(product.price * quantity)}</strong></div>)}</div><div className="cart-page-delivery"><div><Icon name="truck" size={18} /><span>{deliveryMessage}</span></div><div className="progress-track"><span style={{ width: `${progress}%` }} /></div></div></> : <div className="customer-empty-state"><span className="customer-empty-icon"><Icon name="box" size={27} /></span><h3>Tu canasta está vacía</h3><p>Agrega productos del catálogo para comenzar tu compra de la semana.</p><button className="primary-button" type="button" onClick={onBack}>Explorar catálogo <Icon name="arrow" size={17} /></button></div>}
        </section>

        <aside className="cart-page-summary"><span className="customer-eyebrow">Resumen de compra</span><h2>Lista para el sábado</h2><div className="cart-page-summary-rows"><div><span>Subtotal</span><strong>{formatMoney(subtotal)}</strong></div><div><span>Delivery</span><strong className={deliveryFee === 0 ? 'is-free' : ''}>{deliveryFee === 0 ? 'Gratis' : formatMoney(deliveryFee)}</strong></div><div><span>Total estimado</span><strong>{formatMoney(total)}</strong></div></div><button className="primary-button" type="button" onClick={onCheckout} disabled={!lines.length}>Continuar pedido <Icon name="arrow" size={17} /></button><p>Podrás elegir dirección, ventana y pagar con Yape, Plin o contraentrega.</p><button className="text-button" type="button" onClick={onBack}>Agregar más productos <Icon name="arrow" size={16} /></button></aside>
      </div>
    </main>
  );
}

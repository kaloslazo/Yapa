import type { Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { minimumMessage, type CartLine } from './CartPanel';
import { MIN_SUBTOTAL } from '../utils/domain';

interface CartPageProps {
  lines: CartLine[];
  subtotal: number;
  delivery: number;
  total: number;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onCheckout: () => void;
  onBack: () => void;
}

export function CartPage({ lines, subtotal, delivery, total, onAdd, onDecrease, onCheckout, onBack }: CartPageProps) {
  const units = lines.reduce((sum, line) => sum + line.quantity, 0);
  const progress = Math.min((subtotal / MIN_SUBTOTAL) * 100, 100);
  const deliveryMessage = minimumMessage(subtotal);

  return (
    <main className="customer-page" id="cart-page">
      <header className="customer-page-header">
        <div><span className="customer-eyebrow">Tu compra</span><h1>Tu canasta de la semana</h1><p>Pagas el precio máximo; lo que ahorremos entre todos vuelve como saldo después de la entrega.</p></div>
        <div className="customer-page-note"><span className="customer-page-note-icon"><Icon name="calendar" size={20} /></span><span><small>Próxima entrega</small><strong>Sábado · según tu zona</strong></span></div>
      </header>

      <div className="cart-page-grid">
        <section className="customer-main-card" aria-labelledby="cart-page-title">
          <div className="customer-section-heading"><div><span className="customer-eyebrow">Productos elegidos</span><h2 id="cart-page-title">Tu canasta</h2></div><span className="customer-count">{units} {units === 1 ? 'producto' : 'productos'}</span></div>
          {lines.length ? <><div className="cart-page-lines">{lines.map(({ product, quantity }) => <div className="cart-page-line" key={product.id}><div className={`cart-page-art product-visual--${product.art}`}><img src={product.image} alt={product.name} width="720" height="720" /></div><div className="cart-page-line-copy"><strong>{product.name}</strong><span>{product.detail}</span><small>{formatMoney(product.price)} / {product.unit} · máximo</small></div><div className="quantity-control" aria-label={`Cantidad de ${product.name}`}><button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar una unidad de ${product.name}`}><Icon name="minus" size={14} /></button><span>{quantity}</span><button type="button" onClick={() => onAdd(product)} aria-label={`Agregar una unidad de ${product.name}`}><Icon name="plus" size={14} /></button></div><strong className="cart-page-line-total">{formatMoney(product.price * quantity)}</strong></div>)}</div><div className="cart-page-delivery"><div><Icon name="check" size={18} /><span>{deliveryMessage}</span></div><div className="progress-track"><span style={{ width: `${progress}%` }} /></div></div></> : <div className="customer-empty-state"><span className="customer-empty-icon"><Icon name="box" size={27} /></span><h3>Tu canasta está vacía</h3><p>Agrega productos del catálogo para comenzar tu compra de la semana.</p><button className="primary-button" type="button" onClick={onBack}>Explorar catálogo <Icon name="arrow" size={17} /></button></div>}
        </section>

        <aside className="cart-page-summary"><span className="customer-eyebrow">Resumen de compra</span><h2>Lista para el sábado</h2><div className="cart-page-summary-rows"><div><span>Productos a precio máximo</span><strong>{formatMoney(subtotal)}</strong></div><div><span>Envío máximo</span><strong>{formatMoney(delivery)}</strong></div><div><span>Pagas hoy</span><strong>{formatMoney(total)}</strong></div></div><button className="primary-button" type="button" onClick={onCheckout} disabled={!lines.length}>Continuar pedido <Icon name="arrow" size={17} /></button><p>Pagas por adelantado con Yape o Plin. Si tu zona no llega a 8 pedidos, te devolvemos el 100 %.</p><button className="text-button" type="button" onClick={onBack}>Agregar más productos <Icon name="arrow" size={16} /></button></aside>
      </div>
    </main>
  );
}

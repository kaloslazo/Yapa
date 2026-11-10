import type { Product } from '../types';
import { Icon } from './Icon';
import { ProductVisual, unitLabel } from './Catalog';
import { formatMoney } from '../utils/format';
import { formatQuantity, minimumGap } from '../utils/cart';
import { MAX_DELIVERY, MIN_SUBTOTAL, type CartLine } from './CartPanel';

interface CartPageProps {
  lines: CartLine[];
  subtotal: number;
  savings: number;
  busy?: boolean;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onOpen: (product: Product) => void;
  onCheckout: () => void;
  onClear: () => void;
  onBack: () => void;
}

// canasta: primero cuánto falta para el mínimo, después los productos, el resumen y un solo botón
export function CartPage({ lines, subtotal, savings, busy = false, onAdd, onDecrease, onOpen, onCheckout, onClear, onBack }: CartPageProps) {
  const gap = minimumGap(subtotal, MIN_SUBTOTAL);
  const total = subtotal + (lines.length ? MAX_DELIVERY : 0);
  const progress = Math.min((subtotal / MIN_SUBTOTAL) * 100, 100);

  return (
    <main className="page-content cart-view" id="cart-page">
      <div className="page-bar">
        <button className="round-button" type="button" onClick={onBack} aria-label="Seguir comprando"><Icon name="back" size={20} /></button>
        <h1>Tu canasta</h1>
        {lines.length ? <button className="round-button" type="button" onClick={onClear} aria-label="Vaciar la canasta"><Icon name="close" size={19} /></button> : <span className="round-button is-ghost" aria-hidden="true" />}
      </div>

      {lines.length ? (
        <div className="cart-layout">
          <section className="cart-main" aria-label="Productos de tu canasta">
            <div className={`minimum-card ${gap ? '' : 'is-ready'}`}>
              <p>{gap ? <>Te faltan <b>{formatMoney(gap)}</b> para el mínimo de {formatMoney(MIN_SUBTOTAL)}</> : <>Ya pasaste el mínimo de {formatMoney(MIN_SUBTOTAL)} · <b>listo para pedir</b></>}</p>
              <span className="meter" aria-hidden="true"><span style={{ width: `${progress}%` }} /></span>
            </div>
            <ul className="cart-lines">
              {lines.map(({ product, quantity }) => {
                const unit = unitLabel(product.unit);
                return (
                  <li className="cart-line-item" key={product.id}>
                    <button className="cart-line-photo" type="button" onClick={() => onOpen(product)} aria-label={`Ver ${product.name}`}><ProductVisual product={product} className="cart-page-art" /></button>
                    <div className="cart-line-body">
                      <button className="cart-line-name" type="button" onClick={() => onOpen(product)}><strong>{product.name}</strong><small>{formatMoney(product.price)} / {unit}</small></button>
                      <div className="cart-line-row">
                        <strong className="cart-line-total">{formatMoney(product.price * quantity)}</strong>
                        <div className="stepper" aria-label={`Cantidad de ${product.name}`}>
                          <button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={15} weight="bold" /></button>
                          <span>{formatQuantity(quantity)} {unit}</span>
                          <button className="is-plus" type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={15} weight="bold" /></button>
                        </div>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>

          <aside className="cart-side" aria-labelledby="cart-summary-title">
            <h2 id="cart-summary-title">Resumen</h2>
            <dl className="totals">
              <div><dt>Productos</dt><dd>{formatMoney(subtotal)}</dd></div>
              <div><dt>Envío máximo</dt><dd>{formatMoney(MAX_DELIVERY)}</dd></div>
              {savings > 0 ? <div className="is-saving"><dt>Ahorras frente al súper</dt><dd>{formatMoney(savings)}</dd></div> : null}
              <div className="is-total"><dt>Total máximo</dt><dd>{formatMoney(total)}</dd></div>
            </dl>
            <p className="pp-note">Nunca pagas más que esto. Si entre todos el precio baja, te devolvemos la diferencia. Si tu zona no llega a 8 pedidos, te devolvemos el 100 %.</p>
            <div className="sticky-cta">
              <button className="primary-button" type="button" onClick={onCheckout} disabled={gap > 0 || busy} aria-busy={busy}>{gap > 0 ? `Te faltan ${formatMoney(gap)}` : busy ? 'Preparando tu pedido…' : `Ir a pagar · ${formatMoney(total)}`}</button>
            </div>
          </aside>
        </div>
      ) : (
        <div className="shop-empty cart-empty-state">
          <span className="empty-art" aria-hidden="true"><Icon name="basket" size={30} /></span>
          <h3>Tu canasta está vacía</h3>
          <p>Agrega productos de la semana; el mínimo para pedir es {formatMoney(MIN_SUBTOTAL)}.</p>
          <button className="primary-button" type="button" onClick={onBack}>Ver productos</button>
        </div>
      )}
    </main>
  );
}

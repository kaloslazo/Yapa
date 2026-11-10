import type { Product } from '../types';
import { Icon } from './Icon';
import { ProductVisual, savingPercent, unitLabel } from './Catalog';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';
import { dropFill } from '../utils/shop';
import { shortDate } from '../utils/week';

interface ProductPageProps {
  product: Product | undefined;
  quantity: number;
  delivery: string;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onBack: () => void;
  onCart: () => void;
  onShare: (product: Product) => void;
}

// ficha del producto como pantalla propia: foto grande, precio, cantidad y el detalle en secciones que se abren
export function ProductPage({ product, quantity, delivery, onAdd, onDecrease, onBack, onCart, onShare }: ProductPageProps) {
  if (!product) {
    return (
      <main className="page-content product-page is-missing">
        <div className="page-bar"><button className="round-button" type="button" onClick={onBack} aria-label="Volver"><Icon name="back" size={20} /></button><h1>Producto</h1><span className="round-button is-ghost" aria-hidden="true" /></div>
        <div className="shop-empty"><h3>No encontramos este producto</h3><p>Puede que ya no esté en el catálogo de esta semana.</p><button className="secondary-button" type="button" onClick={onBack}>Volver a la tienda</button></div>
      </main>
    );
  }
  const unit = unitLabel(product.unit);
  const per = product.unit === 'kg' ? 'kilo' : product.unit;
  const off = savingPercent(product);
  const tiers = [...product.tiers].sort((a, b) => a.from - b.from);
  const current = tiers.filter((t) => t.from <= product.ordered).pop();
  const next = product.nextTier;
  const fill = dropFill(product);
  return (
    <main className="page-content product-page">
      <div className="pp-media" style={{ background: product.tint }}>
        <div className="pp-bar">
          <button className="round-button" type="button" onClick={onBack} aria-label="Volver"><Icon name="back" size={20} /></button>
          <button className="round-button" type="button" onClick={() => onShare(product)} aria-label={`Compartir ${product.name}`}><Icon name="share" size={19} /></button>
        </div>
        <ProductVisual product={product} className="pp-visual" />
        {off ? <span className="save-tag">−{off}%</span> : null}
      </div>
      <div className="pp-info">
        <div className="pp-title">
          <div><h1>{product.name}</h1><p>{product.detail} · precio por {per}</p></div>
          {quantity ? (
            <div className="stepper" aria-label={`Cantidad de ${product.name}`}>
              <button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={16} weight="bold" /></button>
              <span>{formatQuantity(quantity)} {unit}</span>
              <button className="is-plus" type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={16} weight="bold" /></button>
            </div>
          ) : null}
        </div>
        <div className="pp-price">
          <strong>{formatMoney(product.price)}</strong>
          {off && product.supermarket ? <><s>{formatMoney(product.supermarket.price)}</s><span className="save-chip">Ahorras {formatMoney(product.supermarket.price - product.price)}</span></> : null}
        </div>
        <div className="pp-sections">
          {tiers.length > 1 ? (
            <details open>
              <summary>Cómo baja el precio<Icon name="chevron" size={18} /></summary>
              <ul className="pp-tiers">
                {tiers.map((t) => <li key={t.from} className={t === current ? 'is-current' : ''}><span>{t.from ? `Desde ${formatQuantity(t.from)} ${unit} entre todos` : 'Hoy, al pedir'}</span><span>{formatMoney(t.price)}</span></li>)}
              </ul>
              {next && fill !== null ? <><p className="pp-note">Van {formatQuantity(product.ordered)} {unit} · faltan {formatQuantity(Math.round((next.from - product.ordered) * 100) / 100)} {unit} para el siguiente precio. Si baja, te devolvemos la diferencia.</p><span className="meter" aria-hidden="true"><span style={{ width: `${fill * 100}%` }} /></span></> : <p className="pp-note">Ya llegamos al mejor precio de la semana.</p>}
            </details>
          ) : null}
          {product.supermarket ? (
            <details>
              <summary>Precio en el súper<Icon name="chevron" size={18} /></summary>
              <p className="pp-note">En {product.supermarket.source} cuesta {formatMoney(product.supermarket.price)}{product.supermarket.seen ? ` (lo vimos el ${shortDate(product.supermarket.seen)})` : ''}. En Yapa pagas como máximo {formatMoney(product.price)}.</p>
            </details>
          ) : null}
          <details>
            <summary>Cuándo llega<Icon name="chevron" size={18} /></summary>
            <p className="pp-note">Si pides hasta el miércoles a las 8 p. m., llega el {delivery} a la portería de tu edificio.</p>
          </details>
        </div>
        <p className="pp-note">Hasta {formatQuantity(product.maxPerOrder)} {unit} por vecino, para que alcance para todos.</p>
      </div>
      <div className="pp-cta">
        {quantity ? <button className="primary-button" type="button" onClick={onCart}><Icon name="basket" size={18} />Ver canasta</button>
          : <button className="primary-button" type="button" onClick={() => onAdd(product)}><Icon name="basket" size={18} />Agregar a la canasta · {formatMoney(product.price)}</button>}
      </div>
    </main>
  );
}

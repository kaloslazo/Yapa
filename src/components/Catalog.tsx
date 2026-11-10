import type { CSSProperties } from 'react';
import type { CartState, Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';
import { dropFill } from '../utils/shop';

// piezas de producto de la tienda: tarjeta (grilla y carrusel), fila «por bajar» y grilla

export const unitLabel = (unit: string) => (unit === 'unidad' ? 'u.' : unit);
export const savingPercent = (product: Product) => (product.supermarketSaving && product.supermarket ? Math.round(product.supermarketSaving) : 0);

// galón genérico para la limpieza mientras no haya fotos propias
function JugArt({ colors: [body, cap] }: { colors: [string, string] }) {
  return (
    <svg className="product-jug" viewBox="0 0 120 150" aria-hidden="true">
      <rect x="52" y="6" width="26" height="16" rx="3" fill={cap} />
      <path d="M40 30c0-6 5-10 11-10h28c6 0 11 4 11 10v6l14 14c4 4 6 9 6 14v70c0 7-5 12-12 12H22c-7 0-12-5-12-12V64c0-5 2-10 6-14l24-20Z" fill={body} stroke="rgba(0,0,0,.18)" strokeWidth="2" />
      <path d="M62 34h22c3 0 5 2 5 5v14c0 3-2 5-5 5H62c-3 0-5-2-5-5V39c0-3 2-5 5-5Z" fill="#f4f4f2" stroke="rgba(0,0,0,.18)" strokeWidth="2" />
      <rect x="24" y="78" width="72" height="40" rx="5" fill="#fff" opacity=".92" />
      <rect x="34" y="90" width="52" height="5" rx="2.5" fill={cap} />
      <rect x="34" y="101" width="34" height="5" rx="2.5" fill="#cfcfcf" />
    </svg>
  );
}

export function ProductVisual({ product, className = 'product-visual' }: { product: Product; className?: string }) {
  return (
    <div className={className} style={{ '--tint': product.tint } as CSSProperties}>
      {product.image ? <img className="product-image" src={product.image} alt={product.name} loading="lazy" />
        : product.jug ? <><JugArt colors={product.jug} /><span className="sr-only">{product.name}</span></>
          : <span className="product-fallback" role="img" aria-label={product.name}><Icon name={product.group === 'limpieza' ? 'box' : 'leaf'} size={36} /></span>}
    </div>
  );
}

interface ProductActions {
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onOpen: (product: Product) => void;
}

export function ProductCard({ product, quantity, onAdd, onDecrease, onOpen }: ProductActions & { product: Product; quantity: number }) {
  const off = savingPercent(product);
  const unit = unitLabel(product.unit);
  return (
    <article className={`pcard ${quantity ? 'has-quantity' : ''}`}>
      <div className="pcard-media">
        <button className="pcard-photo" type="button" onClick={() => onOpen(product)} aria-label={`Ver ${product.name}`}><ProductVisual product={product} /></button>
        {off ? <span className="save-tag">−{off}%</span> : null}
        {quantity ? (
          <div className="pcard-qty" aria-label={`Cantidad de ${product.name}`}>
            <button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={15} weight="bold" /></button>
            <span>{formatQuantity(quantity)} {unit}</span>
            <button type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={15} weight="bold" /></button>
          </div>
        ) : <button className="pcard-add" type="button" onClick={() => onAdd(product)} aria-label={`Agregar ${product.name}`}><Icon name="plus" size={18} weight="bold" /></button>}
      </div>
      <button className="pcard-info" type="button" onClick={() => onOpen(product)}>
        <span className="pcard-price">{formatMoney(product.price)} <small>/ {unit}</small></span>
        <span className="pcard-name">{product.name}</span>
        <span className="pcard-ref">{off && product.supermarket ? <>En el súper <s>{formatMoney(product.supermarket.price)}</s></> : product.detail}</span>
      </button>
    </article>
  );
}

// fila de «Están por bajar»: cuánto falta entre todos para el siguiente precio
export function ProductRow({ product, onAdd, onOpen }: Omit<ProductActions, 'onDecrease'> & { product: Product }) {
  const next = product.nextTier;
  const fill = dropFill(product) ?? 1;
  const unit = unitLabel(product.unit);
  return (
    <div className="prow">
      <button className="prow-main" type="button" onClick={() => onOpen(product)}>
        <ProductVisual product={product} className="prow-photo" />
        <span className="prow-copy">
          <strong>{product.name}</strong>
          {next ? <small>Faltan <b>{formatQuantity(Math.round((next.from - product.ordered) * 100) / 100)} {unit}</b> para que baje a {formatMoney(next.price)}</small> : <small>Ya tiene el mejor precio</small>}
          <span className="meter" aria-hidden="true"><span style={{ width: `${fill * 100}%` }} /></span>
        </span>
      </button>
      <button className="prow-add" type="button" onClick={() => onAdd(product)} aria-label={`Agregar ${product.name}`}><Icon name="plus" size={18} weight="bold" /></button>
    </div>
  );
}

export function ProductGrid({ products, cart, onAdd, onDecrease, onOpen, className = '' }: ProductActions & { products: Product[]; cart: CartState; className?: string }) {
  return <div className={`pgrid ${className}`}>{products.map((product) => <ProductCard key={product.id} product={product} quantity={cart[product.id] || 0} onAdd={onAdd} onDecrease={onDecrease} onOpen={onOpen} />)}</div>;
}

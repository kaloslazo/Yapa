import type { CartState, Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';

interface CatalogProps {
  products: Product[];
  categories: string[];
  cart: CartState;
  category: string;
  query: string;
  onCategoryChange: (category: string) => void;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onOpen: (product: Product) => void;
  onClearFilters: () => void;
}

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
    <div className={className}>
      {product.image ? <img className="product-image" src={product.image} alt={product.name} loading="lazy" />
        : product.jug ? <><JugArt colors={product.jug} /><span className="sr-only">{product.name}</span></>
          : <span className="product-fallback" role="img" aria-label={product.name}><Icon name={product.category === 'Limpieza' ? 'box' : 'leaf'} size={36} /></span>}
    </div>
  );
}

export function Catalog({ products, categories, cart, category, query, onCategoryChange, onAdd, onDecrease, onOpen, onClearFilters }: CatalogProps) {
  return (
    <section className="shop" aria-labelledby="catalog-title">
      <h2 id="catalog-title" className="sr-only">Productos de la semana</h2>
      <div className="shop-tabs" role="group" aria-label="Filtrar por categoría">
        {['Todos', ...categories].map((item) => (
          <button key={item} type="button" className={category === item ? 'is-selected' : ''} aria-pressed={category === item} onClick={() => onCategoryChange(item)}>{item === 'Todos' ? 'Todo' : item}</button>
        ))}
      </div>
      {products.length ? (
        <div className="shop-grid">
          {products.map((product) => <ProductCard key={product.id} product={product} quantity={cart[product.id] || 0} onAdd={onAdd} onDecrease={onDecrease} onOpen={onOpen} />)}
        </div>
      ) : (
        <div className="shop-empty">
          <h3>{query.trim() ? `No encontramos «${query.trim()}»` : 'No hay productos en esta categoría'}</h3>
          <p>Prueba con otra palabra o mira todo lo de la semana.</p>
          <button className="secondary-button" type="button" onClick={onClearFilters}>Ver todo</button>
        </div>
      )}
    </section>
  );
}

function ProductCard({ product, quantity, onAdd, onDecrease, onOpen }: { product: Product; quantity: number; onAdd: (product: Product) => void; onDecrease: (product: Product) => void; onOpen: (product: Product) => void }) {
  const off = savingPercent(product);
  const unit = unitLabel(product.unit);
  return (
    <article className={`shop-card ${quantity ? 'has-quantity' : ''}`}>
      <div className="shop-media">
        <button className="shop-photo" type="button" onClick={() => onOpen(product)} aria-label={`Ver ${product.name}`}>
          <ProductVisual product={product} />
        </button>
        {off ? <span className="shop-off">−{off}%</span> : null}
        {quantity ? (
          <div className="shop-stepper" aria-label={`Cantidad de ${product.name}`}>
            <button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={16} weight="bold" /></button>
            <span>{formatQuantity(quantity)} {unit}</span>
            <button type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={16} weight="bold" /></button>
          </div>
        ) : <button className="shop-plus" type="button" onClick={() => onAdd(product)} aria-label={`Agregar ${product.name}`}><Icon name="plus" size={20} weight="bold" /></button>}
      </div>
      <button className="shop-info" type="button" onClick={() => onOpen(product)}>
        <span className="shop-price">{formatMoney(product.price)} <small>/ {unit}</small></span>
        <span className="shop-name">{product.name}</span>
        {off && product.supermarket ? <span className="shop-was">En el súper <s>{formatMoney(product.supermarket.price)}</s></span> : null}
      </button>
    </article>
  );
}

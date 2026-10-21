import type { CartState, Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';
import { shortDate } from '../utils/week';

interface CatalogProps {
  products: Product[];
  categories: string[];
  cart: CartState;
  category: string;
  query: string;
  onCategoryChange: (category: string) => void;
  onQueryChange: (query: string) => void;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onClearFilters: () => void;
}

export function ProductVisual({ product, className = 'product-visual' }: { product: Product; className?: string }) {
  return (
    <div className={`${className} product-visual--${product.art}`}>
      {product.image ? <img className="product-image" src={product.image} alt={product.name} width="720" height="720" loading="lazy" /> : <span className="product-emoji" role="img" aria-label={product.name}>{product.emoji}</span>}
    </div>
  );
}

export function Catalog({ products, categories, cart, category, query, onCategoryChange, onQueryChange, onAdd, onDecrease, onClearFilters }: CatalogProps) {
  return (
    <section className="catalog-column" aria-labelledby="catalog-title">
      <div className="section-heading">
        <div><h2 id="catalog-title">Catálogo de esta semana</h2><p>Pagas el precio máximo. Si entre todos llegamos a un tramo, el precio baja y te devolvemos la diferencia.</p></div>
        <span className="catalog-count">{products.length} {products.length === 1 ? 'producto' : 'productos'}</span>
      </div>
      <div className="catalog-tools">
        <label className="search-field">
          <Icon name="search" size={19} />
          <span className="sr-only">Buscar productos</span>
          <input name="product-search" value={query} onChange={(event) => onQueryChange(event.target.value)} type="search" placeholder="Busca papa, limón, lejía…" autoComplete="off" />
        </label>
        <div className="category-tabs" role="group" aria-label="Filtrar por categoría">
          {['Todos', ...categories].map((item) => (
            <button className={`category-tab ${category === item ? 'is-selected' : ''}`} key={item} type="button" aria-pressed={category === item} onClick={() => onCategoryChange(item)}>{item}</button>
          ))}
        </div>
      </div>
      <div className="product-grid">
        {products.length ? products.map((product) => <ProductCard key={product.id} product={product} quantity={cart[product.id] || 0} onAdd={onAdd} onDecrease={onDecrease} />) : (
          <div className="empty-state"><span className="empty-icon"><Icon name="search" size={24} /></span><h3>No encontramos ese producto</h3><p>Prueba con otra palabra o vuelve a ver todo el catálogo.</p><button className="secondary-button" type="button" onClick={onClearFilters}>Ver todo</button></div>
        )}
      </div>
    </section>
  );
}

function ProductCard({ product, quantity, onAdd, onDecrease }: { product: Product; quantity: number; onAdd: (product: Product) => void; onDecrease: (product: Product) => void }) {
  const atLimit = quantity >= product.maxPerOrder;
  const tier = product.nextTier;
  const progress = tier ? Math.min((product.ordered / tier.from) * 100, 100) : 100;
  return (
    <article className={`product-card ${quantity ? 'has-quantity' : ''}`}>
      <div className="product-visual-wrap">
        <ProductVisual product={product} />
        <span className="product-category">{product.category}</span>
        {product.supermarketSaving ? <span className="saving-badge" title={product.supermarket?.seen ? `Precio de ${product.supermarket.source} visto el ${shortDate(product.supermarket.seen)}` : undefined}><Icon name="tag" size={13} weight="bold" />{Math.round(product.supermarketSaving)} % menos que en {product.supermarket?.source}{product.supermarket?.seen ? <span className="sr-only"> (precio visto el {shortDate(product.supermarket.seen)})</span> : null}</span> : null}
      </div>
      <div className="product-info">
        <div className="product-title-row"><h3>{product.name}</h3>{quantity ? <span className="in-cart-label">{formatQuantity(quantity)} {product.unit}</span> : null}</div>
        <p>{product.detail}</p>
        <div className="tier-progress" aria-label={tier ? `Entre todos llevamos ${formatQuantity(product.ordered)} de ${tier.from} ${product.unit}` : 'Ya estamos en el mejor precio'}>
          <div className="tier-progress-copy"><Icon name="users" size={14} />{tier ? <span>Vamos {formatQuantity(product.ordered)} de {tier.from} {product.unit} · baja a <strong className="nowrap">{formatMoney(tier.price)}</strong></span> : <span><strong>¡Mejor precio alcanzado!</strong></span>}</div>
          <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
        </div>
        <div className="product-buy-row">
          <div><strong>{formatMoney(product.price)}</strong><span>/ {product.unit} · máximo</span></div>
          {quantity ? (
            <div className="quantity-control" aria-label={`Cantidad de ${product.name}`}>
              <button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={14} /></button>
              <span>{formatQuantity(quantity)}</span>
              <button type="button" onClick={() => onAdd(product)} disabled={atLimit} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={14} /></button>
            </div>
          ) : <button className="add-button" type="button" onClick={() => onAdd(product)}>Agregar</button>}
        </div>
      </div>
    </article>
  );
}

import { categories } from '../types';
import type { CartState, Category, Product } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { maxPerLine, nextTier } from '../utils/domain';

interface CatalogProps {
  products: Product[];
  cart: CartState;
  category: Category;
  query: string;
  onCategoryChange: (category: Category) => void;
  onQueryChange: (query: string) => void;
  onAdd: (product: Product) => void;
  onClearFilters: () => void;
}

export function Catalog({ products, cart, category, query, onCategoryChange, onQueryChange, onAdd, onClearFilters }: CatalogProps) {
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
          <input name="product-search" value={query} onChange={(event) => onQueryChange(event.target.value)} type="search" placeholder="Busca arroz, fruta, verduras…" autoComplete="off" />
        </label>
        <div className="category-tabs" role="tablist" aria-label="Filtrar por categoría">
          {categories.map((item) => (
            <button className={`category-tab ${category === item ? 'is-selected' : ''}`} key={item} type="button" role="tab" aria-selected={category === item} onClick={() => onCategoryChange(item)}>{item}</button>
          ))}
        </div>
      </div>
      <div className="product-grid">
        {products.length ? products.map((product) => <ProductCard key={product.id} product={product} quantity={cart[product.id] || 0} onAdd={onAdd} />) : (
          <div className="empty-state"><span className="empty-icon"><Icon name="search" size={24} /></span><h3>No encontramos ese producto</h3><p>Prueba con otra palabra o vuelve a ver todo el catálogo.</p><button className="secondary-button" type="button" onClick={onClearFilters}>Ver todo</button></div>
        )}
      </div>
    </section>
  );
}

function ProductCard({ product, quantity, onAdd }: { product: Product; quantity: number; onAdd: (product: Product) => void }) {
  const unavailable = product.stock <= 0;
  const limit = Math.min(product.stock, maxPerLine(product));
  const tier = nextTier(product);
  return (
    <article className={`product-card ${quantity ? 'has-quantity' : ''} ${unavailable ? 'is-unavailable' : ''}`}>
      <div className={`product-visual product-visual--${product.art}`}><img className="product-image" src={product.image} alt={product.name} width="720" height="720" loading="lazy" /><span className="product-category">{product.category}</span></div>
      <div className="product-info">
        <div className="product-title-row"><h3>{product.name}</h3>{quantity ? <span className="in-cart-label">{quantity} en canasta</span> : null}</div>
        <p>{product.detail}</p>
        {tier ? <p className="tier-note"><Icon name="arrow" size={13} weight="bold" />Si entre todos pedimos {tier.from} {product.unit}, baja a {formatMoney(tier.price)}</p> : null}
        <div className="product-buy-row"><div><strong>{formatMoney(product.price)}</strong><span>/ {product.unit} · máximo</span></div><button className="add-button" type="button" onClick={() => onAdd(product)} disabled={unavailable || quantity >= limit}>{unavailable ? 'Agotado' : quantity >= limit ? 'Tope' : quantity ? <><Icon name="plus" size={17} /><span className="sr-only">Agregar otra unidad</span></> : 'Agregar'}</button></div>
      </div>
    </article>
  );
}

import { useState } from 'react';
import type { CartState, Product } from '../types';
import { Icon } from './Icon';
import { ProductGrid, ProductVisual, savingPercent } from './Catalog';
import { groups } from '../data/presentation';
import { formatMoney } from '../utils/format';
import { bestDeals } from '../utils/landing';
import { applyChip, inGroup, type Chip } from '../utils/shop';

interface ExplorePageProps {
  products: Product[];
  group: string | null;
  initialChip?: Chip;
  cart: CartState;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onOpen: (product: Product) => void;
  onGroup: (group: string | null) => void;
}

const CHIPS: Array<{ id: Chip; label: string }> = [
  { id: 'todo', label: 'Todo' },
  { id: 'ahorro', label: 'Más ahorro' },
  { id: 'por-bajar', label: 'Por bajar' },
];

// Explorar (sin grupo): la oferta de la semana, las categorías y todo con filtros; con grupo, la categoría
export function ExplorePage({ products, group, initialChip = 'todo', cart, onAdd, onDecrease, onOpen, onGroup }: ExplorePageProps) {
  const [chip, setChip] = useState<Chip>(initialChip);
  const meta = groups.find((g) => g.id === group);
  const list = applyChip(meta ? inGroup(products, meta.id) : products, chip);
  const top = bestDeals(products, 1)[0];
  const actions = { onAdd, onDecrease, onOpen };
  const chips = (
    <div className="chips" role="group" aria-label="Ordenar">
      {CHIPS.map((c) => <button key={c.id} type="button" className={chip === c.id ? 'is-on' : ''} aria-pressed={chip === c.id} onClick={() => setChip(c.id)}>{c.label}</button>)}
    </div>
  );

  if (meta) {
    return (
      <main className="page-content explore">
        <div className="page-bar"><button className="round-button" type="button" onClick={() => onGroup(null)} aria-label="Volver a Explorar"><Icon name="back" size={20} /></button><h1>{meta.name}</h1><span className="round-button is-ghost" aria-hidden="true" /></div>
        {chips}
        {list.length ? <ProductGrid products={list} cart={cart} {...actions} /> : <div className="shop-empty"><h3>Nada por aquí esta semana</h3><p>Mira las otras categorías.</p></div>}
      </main>
    );
  }

  return (
    <main className="page-content explore">
      <div className="page-bar is-start"><h1>Explorar</h1></div>
      {top && top.supermarket ? (
        <button className="promo" type="button" onClick={() => onOpen(top)}>
          <span><strong>{top.name} a {formatMoney(top.price)}</strong><small>{savingPercent(top)} % menos que en el súper. Solo esta semana.</small></span>
          <ProductVisual product={top} className="promo-photo" />
        </button>
      ) : null}
      <div className="cat-grid">
        {groups.map((g) => {
          const items = inGroup(products, g.id);
          return <button key={g.id} className="cat-card" type="button" style={{ background: g.tint }} onClick={() => onGroup(g.id)}><strong>{g.name}</strong><small>{items.length} {items.length === 1 ? 'producto' : 'productos'}</small>{items[0] ? <ProductVisual product={items[0]} className="cat-card-photo" /> : null}</button>;
        })}
      </div>
      <div className="sec-head"><h2>Todos los productos</h2></div>
      {chips}
      <ProductGrid products={list} cart={cart} {...actions} />
    </main>
  );
}

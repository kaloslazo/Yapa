import type { ReactNode } from 'react';
import type { CartState, Product } from '../types';
import { Icon } from './Icon';
import { ProductCard, ProductGrid, ProductRow, ProductVisual } from './Catalog';
import { groups } from '../data/presentation';
import { formatMoney } from '../utils/format';
import { bestDeals } from '../utils/landing';
import { inGroup, nearDrop, type Chip } from '../utils/shop';

interface HomePageProps {
  products: Product[];
  results: Product[];
  query: string;
  cart: CartState;
  cycleOpen: boolean;
  countdown: string;
  delivery: string;
  signedIn: boolean;
  balance: number;
  group?: { verified: number; minimum: number } | null; // iteración 62: avance del grupo del vecino
  assistant?: ReactNode;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onOpen: (product: Product) => void;
  onGroup: (group: string) => void;
  onExplore: (chip?: Chip) => void;
  onHow: () => void;
  onLogin: () => void;
  onBalance: () => void;
  onClearSearch: () => void;
}

const capital = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

// inicio: la semana arriba, después categorías y secciones; con una búsqueda, solo los resultados
export function HomePage(props: HomePageProps) {
  const { products, results, query, cart, onAdd, onDecrease, onOpen } = props;
  const actions = { onAdd, onDecrease, onOpen };
  const deals = bestDeals(products, 6);
  const near = nearDrop(products, 3);
  return (
    <main id="catalog" className="page-content home">
      <h1 id="page-title" className="sr-only">Comprar en Yapa</h1>
      {query.trim() ? (
        <section aria-labelledby="results-title">
          <div className="sec-head"><h2 id="results-title">Resultados para «{query.trim()}»</h2><button type="button" onClick={props.onClearSearch}>Limpiar</button></div>
          {results.length ? <ProductGrid products={results} cart={cart} {...actions} /> : (
            <div className="shop-empty"><h3>No encontramos «{query.trim()}»</h3><p>Prueba con otra palabra o mira las categorías.</p><button className="secondary-button" type="button" onClick={() => props.onExplore()}>Ver categorías</button></div>
          )}
        </section>
      ) : <>
        <WeekCard {...props} />
        {props.assistant}
        <section aria-labelledby="cats-title">
          <div className="sec-head"><h2 id="cats-title">Categorías</h2><button type="button" onClick={() => props.onExplore()}>Ver todo</button></div>
          <div className="cat-row">
            {groups.map((group) => {
              const cover = inGroup(products, group.id)[0];
              return <button key={group.id} className="cat-tile" type="button" onClick={() => props.onGroup(group.id)}><span className="cat-tile-img" style={{ background: group.tint }}>{cover ? <ProductVisual product={cover} /> : null}</span>{group.name}</button>;
            })}
          </div>
        </section>
        {deals.length ? (
          <section aria-labelledby="deals-title">
            <div className="sec-head"><h2 id="deals-title">Mejores precios</h2><button type="button" onClick={() => props.onGroup('ofertas')}>Ver todo</button></div>
            <div className="hscroll">{deals.map((product) => <ProductCard key={product.id} product={product} quantity={cart[product.id] || 0} {...actions} />)}</div>
          </section>
        ) : null}
        {near.length ? (
          <section aria-labelledby="near-title">
            <div className="sec-head"><h2 id="near-title">Están por bajar</h2><button type="button" onClick={() => props.onExplore('por-bajar')}>Ver todo</button></div>
            <div className="prows">{near.map((product) => <ProductRow key={product.id} product={product} onAdd={onAdd} onOpen={onOpen} />)}</div>
          </section>
        ) : null}
        <section aria-labelledby="all-title">
          <div className="sec-head"><h2 id="all-title">Todo lo de esta semana</h2></div>
          <ProductGrid products={products} cart={cart} {...actions} />
        </section>
      </>}
    </main>
  );
}

// la semana en una tarjeta: cuándo cierra y cuándo llega; abajo el saldo o cómo funciona
function WeekCard({ cycleOpen, countdown, delivery, signedIn, balance, group, onHow, onLogin, onBalance }: HomePageProps) {
  return (
    <section className="week-card" aria-label="Esta semana">
      <div className="week-card-top">
        <div><small>{cycleOpen ? 'Pedidos hasta el miércoles 8 p. m.' : 'Esta semana ya se compró'}</small><strong>{cycleOpen ? countdown : 'Abrimos el lunes'}</strong></div>
        <div className="week-card-arrive"><small>Llega a tu portería</small><strong>{capital(delivery)}</strong></div>
      </div>
      {cycleOpen && group ? <GroupLine {...group} /> : null}
      <div className="week-card-foot">
        {signedIn && balance > 0 ? <button className="week-card-balance" type="button" onClick={onBalance}><span>Tienes <b>{formatMoney(balance)}</b> de saldo para tu próxima compra</span><Icon name="arrow" size={16} /></button> : <>
          <p>Pagas el precio máximo. Si entre todos baja, te devolvemos la diferencia.</p>
          <div className="week-card-links"><button type="button" onClick={onHow}>Cómo funciona</button>{signedIn ? null : <button type="button" onClick={onLogin}>Ya tengo cuenta</button>}</div>
        </>}
      </div>
    </section>
  );
}

// cuántos pedidos verificados lleva el grupo frente al mínimo; solo con el ciclo abierto (S-321)
function GroupLine({ verified, minimum }: { verified: number; minimum: number }) {
  const reached = verified >= minimum;
  return (
    <div className="week-card-group">
      <p>{reached ? <>Tu edificio ya llegó a los <b>{minimum} pedidos</b> para comprar juntos</> : <>Tu edificio lleva <b>{verified} de {minimum}</b> pedidos para comprar juntos</>}</p>
      <span className="meter" aria-hidden="true"><span style={{ width: `${Math.min(verified / minimum, 1) * 100}%` }} /></span>
    </div>
  );
}

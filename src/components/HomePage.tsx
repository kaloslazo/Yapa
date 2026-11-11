import type { CSSProperties, ReactNode } from 'react';
import type { CartState, Product } from '../types';
import { Icon, type IconName } from './Icon';
import { ProductCard, ProductGrid, ProductRow, ProductVisual, savingPercent, unitLabel } from './Catalog';
import { RollingNumber, useInView } from './motion';
import { groups } from '../data/presentation';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';
import { bestDeals, type CountdownPart } from '../utils/landing';
import { inGroup, nearDrop, type Chip } from '../utils/shop';

interface HomePageProps {
  products: Product[];
  results: Product[];
  query: string;
  cart: CartState;
  cycleOpen: boolean;
  countdown: string;
  countdownParts?: CountdownPart[];
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
const HERO_PHOTOS = ['PAPA-AMARILLA', 'CEBOLLA-ROJA', 'ZANAHORIA']; // la tarjeta de la semana: tres fotos de colores distintos

// inicio: la semana y la mejor oferta arriba, después categorías y secciones; con una búsqueda, solo los resultados
export function HomePage(props: HomePageProps) {
  const { products, results, query, cart, onAdd, onDecrease, onOpen } = props;
  const actions = { onAdd, onDecrease, onOpen };
  const deals = bestDeals(products, 6);
  const near = nearDrop(products, 3);
  const top = deals[0];
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
        <div className="home-hero">
          <WeekCard {...props} />
          {top ? <Spotlight product={top} quantity={cart[top.id] || 0} onAdd={onAdd} onOpen={onOpen} /> : null}
        </div>
        {props.assistant}
        <Section id="cats-title" title="Categorías" icon="grid" action={<button type="button" onClick={() => props.onExplore()}>Ver todo</button>}>
          <div className="cat-row">
            {groups.map((group, i) => {
              const items = inGroup(products, group.id);
              const cover = items.find((p) => p.image) ?? items[0];
              return (
                <button key={group.id} className="cat-tile" type="button" style={{ '--i': i } as CSSProperties} onClick={() => props.onGroup(group.id)}>
                  <span className="cat-tile-img" style={{ background: group.tint }}>{cover ? <ProductVisual product={cover} /> : null}</span>
                  <span className="cat-tile-copy"><span>{group.name}</span><small>{items.length} {items.length === 1 ? 'producto' : 'productos'}</small></span>
                </button>
              );
            })}
          </div>
        </Section>
        {deals.length ? (
          <Section id="deals-title" title="Mejores precios" icon="tag" action={<button type="button" onClick={() => props.onGroup('ofertas')}>Ver todo</button>}>
            <div className="hscroll">{deals.map((product, i) => <ProductCard key={product.id} index={i} product={product} quantity={cart[product.id] || 0} {...actions} />)}</div>
          </Section>
        ) : null}
        {near.length ? (
          <Section id="near-title" title="Están por bajar" icon="users" action={<button type="button" onClick={() => props.onExplore('por-bajar')}>Ver todo</button>}>
            <div className="prows">{near.map((product, i) => <ProductRow key={product.id} index={i} product={product} onAdd={onAdd} onOpen={onOpen} />)}</div>
          </Section>
        ) : null}
        <Section id="all-title" title="Todo lo de esta semana" icon="basket">
          <ProductGrid products={products} cart={cart} {...actions} />
        </Section>
      </>}
    </main>
  );
}

// sección del inicio: título con su ícono y las tarjetas entran en cascada al verse
function Section({ id, title, icon, action, children }: { id: string; title: string; icon: IconName; action?: ReactNode; children: ReactNode }) {
  const [ref, inView] = useInView<HTMLElement>();
  return (
    <section ref={ref} className={`home-sec ${inView ? 'is-in' : ''}`} aria-labelledby={id}>
      <div className="sec-head"><h2 id={id}><span className={`sec-icon is-${icon}`} aria-hidden="true"><Icon name={icon} size={17} /></span>{title}</h2>{action}</div>
      {children}
    </section>
  );
}

// la semana en una tarjeta: cuánto falta para el cierre, cuándo llega y cómo va el edificio
function WeekCard({ cycleOpen, countdown, countdownParts = [], delivery, signedIn, balance, group, products, onHow, onLogin, onBalance }: HomePageProps) {
  const withPhoto = products.filter((p) => p.image);
  const picked = HERO_PHOTOS.map((id) => withPhoto.find((p) => p.id === id)).filter((p): p is Product => Boolean(p));
  const photos = picked.length === HERO_PHOTOS.length ? picked : withPhoto.slice(0, 3);
  return (
    <section className={`week-card ${photos.length ? 'has-photos' : ''}`} aria-label="Esta semana">
      <div className="week-card-main">
        <span className="week-card-label"><Icon name="calendar" size={16} />{cycleOpen ? 'Pedidos hasta el miércoles 8 p. m.' : 'Esta semana ya se compró'}</span>
        {cycleOpen ? (
          <div className="week-card-count">
            <h2>Esta semana cierra en</h2>
            <p className="sr-only">{countdown}</p>
            {countdownParts.length ? (
              <div className="countdown" aria-hidden="true">
                {countdownParts.map((part) => <span className="countdown-cell" key={part.unit}><RollingNumber value={String(part.value).padStart(2, '0')} /><small>{part.unit}</small></span>)}
              </div>
            ) : <strong className="countdown-text" aria-hidden="true">{countdown}</strong>}
          </div>
        ) : <h2 className="week-card-closed">Abrimos el lunes</h2>}
        <p className="week-card-arrive"><Icon name="truck" size={18} /><span>Llega a tu portería el</span> <b>{capital(delivery)}</b></p>
        {cycleOpen && group ? <GroupLine {...group} /> : null}
        <div className="week-card-foot">
          {signedIn && balance > 0 ? <button className="week-card-balance" type="button" onClick={onBalance}><span>Tienes <b>{formatMoney(balance)}</b> de saldo para tu próxima compra</span><Icon name="arrow" size={16} /></button> : <>
            <p>Pagas el precio máximo. Si entre todos baja, te devolvemos la diferencia.</p>
            <div className="week-card-links"><button type="button" onClick={onHow}>Cómo funciona</button>{signedIn ? null : <button type="button" onClick={onLogin}>Ya tengo cuenta</button>}</div>
          </>}
        </div>
      </div>
      {photos.length ? (
        <div className="week-card-photos" aria-hidden="true">
          {photos.map((product, i) => <span className="week-photo" key={product.id} style={{ '--tint': product.tint, '--i': i } as CSSProperties}><img src={product.image ?? ''} alt="" /></span>)}
        </div>
      ) : null}
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

// la oferta más fuerte de la semana, grande y con su botón
function Spotlight({ product, quantity, onAdd, onOpen }: { product: Product; quantity: number; onAdd: (product: Product) => void; onOpen: (product: Product) => void }) {
  const off = savingPercent(product);
  return (
    <section className="spotlight" style={{ '--tint': product.tint } as CSSProperties} aria-labelledby="spotlight-title">
      <button className="spotlight-photo" type="button" onClick={() => onOpen(product)} aria-label={`Ver ${product.name}`}><ProductVisual product={product} /></button>
      <div className="spotlight-copy">
        <small>La más barata de la semana</small>
        <h2 id="spotlight-title">{product.name}</h2>
        <p><strong>{formatMoney(product.price)}</strong> / {unitLabel(product.unit)}{off ? <span className="spotlight-off">−{off}% frente al súper</span> : null}</p>
      </div>
      <div className="spotlight-cta">
        <button className="spotlight-add" type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder}><Icon name="plus" size={18} weight="bold" />Agregar</button>
        {quantity ? <small>Ya tienes {formatQuantity(quantity)} {unitLabel(product.unit)}</small> : null}
      </div>
    </section>
  );
}

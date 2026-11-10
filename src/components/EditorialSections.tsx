import { Icon } from './Icon';
import type { Product } from '../types';
import { formatMoney } from '../utils/format';
import { bestDeals } from '../utils/landing';

// la semana de Yapa como un calendario: qué pasa cada día (S-02, C-12, S-10, C-05)
const week = [
  { day: 'Lun – Mié', title: 'Pides y pagas', text: 'Arma tu canasta y paga con Yape o Plin hasta el miércoles a las 8 p. m.' },
  { day: 'Jueves', title: 'Compramos al por mayor', text: 'Juntamos los pedidos de todos los edificios y compramos en el mayorista.' },
  { day: 'Viernes', title: 'Armamos tu bolsa', text: 'Cada bolsa lleva tu número de pedido y una foto, para que sepas qué va.' },
  { day: 'Sábado', title: 'Llega a tu portería', text: 'El reparto deja el pedido de todo el edificio y la portería lo recibe.' },
  { day: 'Después', title: 'Te devolvemos', text: 'Si entre todos bajó el precio, la diferencia vuelve a tu saldo.' },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="week-section" aria-labelledby="how-title">
      <div className="section-intro"><span className="eyebrow">Cómo funciona</span><h2 id="how-title">Tu semana con Yapa</h2></div>
      <ol className="week-strip">
        {week.map((item) => (
          <li key={item.day}>
            <span className="week-day">{item.day}</span>
            <h3>{item.title}</h3>
            <p>{item.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

// los precios de la semana tal como vienen del catálogo: es lo primero que hay que ver, no una ilustración
export function PriceBoard({ products }: { products: Product[] }) {
  const deals = bestDeals(products, 5);
  if (!deals.length) return null;
  return (
    <aside className="price-board" aria-labelledby="board-title">
      <div className="price-board-head"><h2 id="board-title">Pizarra de esta semana</h2><span>vs. supermercado</span></div>
      <ul>
        {deals.map((p) => (
          <li key={p.id}>
            <span className="board-name">{p.name}<small>por {p.unit}</small></span>
            <s className="board-ref">{formatMoney(p.supermarket?.price ?? 0)}</s>
            <strong className="board-price">{formatMoney(p.price)}</strong>
            <span className="board-saving">−{Math.round(p.supermarketSaving ?? 0)}%</span>
          </li>
        ))}
      </ul>
      <p className="price-board-foot">Precios máximos de Yapa. Si entre todos pedimos más, bajan.</p>
    </aside>
  );
}

// ejemplo con los números de una semana del piloto (simulado): lo que pagas, lo que costó y lo que vuelve
export function ReturnExample() {
  return (
    <section className="return-section" aria-labelledby="return-title">
      <div className="section-intro">
        <span className="eyebrow">Te devolvemos</span>
        <h2 id="return-title">Pagas el máximo. Lo que sobra, vuelve.</h2>
        <p>Al pedir pagas el precio más alto posible, así nunca te cobramos de más. Cuando sabemos cuánto costó de verdad, te devolvemos la diferencia como saldo para tu próxima compra.</p>
      </div>
      <div className="receipt" role="img" aria-label="Ejemplo: pagaste 61 soles, costó 60.44, te devolvimos 0.56; en el supermercado costaba 102.75">
        <div className="receipt-head"><strong>yapa</strong><span>Pedido de ejemplo · 3 productos</span></div>
        <dl>
          <div><dt>Pagaste al pedir</dt><dd>S/ 61.00</dd></div>
          <div><dt>Costó de verdad</dt><dd>S/ 60.44</dd></div>
          <div className="receipt-total"><dt>Te devolvimos</dt><dd>S/ 0.56</dd></div>
        </dl>
        <div className="receipt-compare"><span>En el supermercado costaba <s>S/ 102.75</s></span><strong>Ahorraste S/ 42.31</strong></div>
        <small>Números de una semana simulada del piloto.</small>
      </div>
    </section>
  );
}

// las garantías viven aquí para no repetirlas en cada bloque de la portada
export const faqs = [
  { q: '¿Cuánto voy a pagar?', a: 'Lo que ves en tu canasta es el máximo. Si entre todos pedimos más y el precio baja, el 75 % de esa baja vuelve a tu saldo después de la entrega; el 25 % sostiene la operación de Yapa.' },
  { q: '¿Qué pasa si mi grupo no llega al mínimo?', a: 'Cada grupo necesita 8 pedidos. Si no llegamos, te devolvemos el 100 % a tu Yape o Plin, o como saldo si lo prefieres.' },
  { q: '¿Dónde y cuándo entregan?', a: 'Los sábados, en la portería de tu edificio, en Lince y Jesús María. La Victoria abre pronto.' },
  { q: '¿Cómo sé que llegó mi pedido?', a: 'Cada entrega queda registrada con foto. Si algo faltó, lo reclamas desde Mis pedidos.' },
  { q: '¿Puedo cancelar?', a: 'Sí, hasta el miércoles a las 20:00 desde Mis pedidos, y te devolvemos todo.' },
  { q: '¿Cómo me registro?', a: 'Con el enlace de invitación de un vecino o del admin de tu edificio. Usas tu correo o tu cuenta de Google.' },
  { q: '¿Qué hago con mi saldo?', a: 'Lo usas en tu próxima compra o lo pides de vuelta a tu Yape o Plin.' },
];

export function FaqSection() {
  return (
    <section className="faq-section" aria-labelledby="faq-title">
      <div className="section-intro"><span className="eyebrow">Dudas</span><h2 id="faq-title">Preguntas frecuentes</h2><p>Lo que más nos preguntan los vecinos antes de su primer pedido.</p></div>
      <div className="faq-list">
        {faqs.map((item) => <details key={item.q}><summary>{item.q}<Icon name="plus" size={18} /></summary><p>{item.a}</p></details>)}
      </div>
    </section>
  );
}

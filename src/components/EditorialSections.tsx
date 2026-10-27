import { Icon } from './Icon';

const steps = [
  { title: 'Arma tu canasta', text: 'Ves el precio máximo de cada producto y hasta dónde puede bajar si entre todos pedimos más.' },
  { title: 'Paga con Yape o Plin', text: 'Antes del miércoles a las 20:00, con el código que te damos al confirmar. Si tu grupo no llega a 8 pedidos, te devolvemos el 100 %.' },
  { title: 'Recibe y te devolvemos', text: 'El sábado llega a tu portería, con foto de la entrega. El ahorro por volumen y lo que sobre del envío vuelven a tu saldo.' },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="how-section" aria-labelledby="how-title">
      <div className="section-intro">
        <h2 id="how-title">Así funciona</h2>
        <p>Compras junto con tus vecinos. Pagas el precio máximo y lo que ahorremos entre todos vuelve como saldo.</p>
      </div>
      <ol className="how-steps">
        {steps.map((step, index) => (
          <li key={step.title}>
            <span className="step-number">{String(index + 1).padStart(2, '0')}</span>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

const guarantees = [
  { icon: 'tag', title: 'Nunca pagas más de lo que ves', text: 'El precio de la canasta es el máximo. Si al final cuesta menos, la diferencia vuelve a tu saldo.' },
  { icon: 'undo', title: 'Si el grupo no llega, te devolvemos todo', text: 'Sin letra chica: el 100 % a tu Yape, Plin o saldo, como prefieras.' },
  { icon: 'camera', title: 'Entrega con foto', text: 'Cada bolsa y cada entrega quedan registradas. Si algo faltó, lo reclamas desde la app.' },
] as const;

export function GuaranteeSection() {
  return (
    <section className="guarantee-section" aria-labelledby="guarantee-title">
      <div className="section-intro">
        <h2 id="guarantee-title">Comprar en grupo, sin riesgo</h2>
        <p>Pagas por adelantado, así que estas reglas no se negocian.</p>
      </div>
      <ul className="guarantee-list">
        {guarantees.map((item) => (
          <li key={item.title}><Icon name={item.icon} size={24} weight="duotone" /><h3>{item.title}</h3><p>{item.text}</p></li>
        ))}
      </ul>
    </section>
  );
}

const faqs = [
  { q: '¿Cómo me registro?', a: 'Con el enlace de invitación de un vecino o del admin de tu edificio. Te registras con tu correo o con Google en un minuto.' },
  { q: '¿Dónde entregan?', a: 'En Lince y Jesús María, en la portería de tu edificio, los sábados. La Victoria abre muy pronto.' },
  { q: '¿Qué pasa si mi grupo no llega al mínimo?', a: 'Te devolvemos el 100 % de lo que pagaste, a tu Yape o Plin o como saldo para la siguiente semana.' },
  { q: '¿Puedo cancelar?', a: 'Sí, hasta el miércoles a las 20:00 desde Mis pedidos, y te devolvemos todo.' },
  { q: '¿Qué es el saldo?', a: 'Lo que ahorramos entre todos y lo que sobra del envío. Lo usas en tu próxima compra o lo pides de vuelta a tu Yape o Plin.' },
];

export function FaqSection() {
  return (
    <section className="faq-section" aria-labelledby="faq-title">
      <div className="section-intro"><h2 id="faq-title">Preguntas frecuentes</h2></div>
      <div className="faq-list">
        {faqs.map((item) => <details key={item.q}><summary>{item.q}<Icon name="plus" size={18} /></summary><p>{item.a}</p></details>)}
      </div>
    </section>
  );
}

export function FinalCta({ onStart, onLogin }: { onStart: () => void; onLogin: () => void }) {
  return (
    <section className="final-cta" aria-labelledby="cta-title">
      <h2 id="cta-title">Esta semana, compra mejor.</h2>
      <p>Pedidos abiertos de lunes a miércoles. Entregamos el sábado.</p>
      <div className="hero-actions"><button className="primary-button" type="button" onClick={onStart}>Armar mi canasta <Icon name="arrow" size={17} /></button><button className="secondary-button secondary-button--light" type="button" onClick={onLogin}>Entrar</button></div>
    </section>
  );
}

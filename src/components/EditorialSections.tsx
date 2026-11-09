import { Icon } from './Icon';

const steps = [
  { title: 'Arma tu canasta', text: 'Cada producto muestra su precio máximo y hasta dónde puede bajar si entre todos pedimos más.' },
  { title: 'Paga con Yape o Plin', text: 'Hasta el miércoles a las 20:00, con el código que te damos al confirmar.' },
  { title: 'Recibe el sábado', text: 'Llega a la portería de tu edificio. Lo que ahorramos entre todos vuelve a tu saldo.' },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="how-section" aria-labelledby="how-title">
      <h2 id="how-title">Así funciona</h2>
      <ol className="how-steps">
        {steps.map((step) => (
          <li key={step.title}>
            <h3>{step.title}</h3>
            <p>{step.text}</p>
          </li>
        ))}
      </ol>
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
      <h2 id="faq-title">Preguntas frecuentes</h2>
      <div className="faq-list">
        {faqs.map((item) => <details key={item.q}><summary>{item.q}<Icon name="plus" size={18} /></summary><p>{item.a}</p></details>)}
      </div>
    </section>
  );
}

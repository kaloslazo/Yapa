import { Icon } from './Icon';

// la semana de Yapa en cuatro pasos (S-02, C-12, S-10, C-05); vive en la hoja «Cómo funciona», no en la portada
const steps = [
  { title: 'Pides hasta el miércoles', text: 'Eliges tus productos y pagas con Yape o Plin hasta las 8 p. m.' },
  { title: 'Compramos al por mayor', text: 'Juntamos los pedidos de todos los edificios y vamos al mayorista.' },
  { title: 'Llega el sábado', text: 'Lo dejamos en la portería de tu edificio, con tu número de pedido y una foto.' },
  { title: 'Si baja, te devolvemos', text: 'Si entre todos el precio bajó, la diferencia vuelve a tu saldo.' },
];

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

export function HowItWorks() {
  return (
    <div className="how-sheet">
      <h2 className="sheet-title">Cómo funciona</h2>
      <ol className="how-list">
        {steps.map((step) => <li key={step.title}><strong>{step.title}</strong><span>{step.text}</span></li>)}
      </ol>
      <h3 className="how-faq-title">Preguntas frecuentes</h3>
      <div className="faq-list">
        {faqs.map((item) => <details key={item.q}><summary>{item.q}<Icon name="plus" size={18} /></summary><p>{item.a}</p></details>)}
      </div>
    </div>
  );
}

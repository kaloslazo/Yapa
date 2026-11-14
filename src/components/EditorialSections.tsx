import { Icon } from './Icon';
import { useState } from 'react';

// la semana de Yapa en cuatro pasos (S-02, C-12, S-10, C-05); vive en la hoja «Cómo funciona», no en la portada
const steps = [
  { title: 'Pides hasta el miércoles', text: 'Eliges tus productos y pagas con Yape o Plin hasta las 8 p. m.' },
  { title: 'Compramos al por mayor', text: 'Juntamos los pedidos de todos los edificios y vamos al mayorista.' },
  { title: 'Llega el sábado', text: 'Lo dejamos en la portería de tu edificio, con tu número de pedido y una foto.' },
  { title: 'Si baja, te devolvemos', text: 'Si entre todos el precio bajó, la diferencia vuelve a tu saldo.' },
];

// las garantías viven aquí para no repetirlas en cada bloque de la portada
import { faqs } from '../data/faqs';
export { faqs } from '../data/faqs';

export function HowItWorks() {
  return (
    <div className="how-sheet">
      <h2 className="sheet-title">Cómo funciona</h2>
      <ol className="how-list">
        {steps.map((step) => <li key={step.title}><strong>{step.title}</strong><span>{step.text}</span></li>)}
      </ol>
      <h3 className="how-faq-title">Preguntas frecuentes</h3>
      <FrequentlyAskedQuestions />
    </div>
  );
}

// una sola lista de preguntas para Explorar y Cómo funciona
export function FrequentlyAskedQuestions({ compact = false }: { compact?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const shown = compact && !expanded ? faqs.slice(0, 5) : faqs;
  return (
    <>
      <div className={`faq-list${compact ? ' faq-list--compact' : ''}`}>
        {shown.map((item) => <details key={item.q}><summary>{item.q}<Icon name="plus" size={18} /></summary><p>{item.a}</p></details>)}
      </div>
      {compact ? <button className="text-button faq-more" type="button" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? 'Ver menos preguntas' : `Ver todas las preguntas (${faqs.length})`}</button> : null}
    </>
  );
}

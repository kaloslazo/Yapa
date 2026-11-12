import { shoppingGuides } from '../data/shoppingGuides';
import { FrequentlyAskedQuestions } from './EditorialSections';
import { Icon } from './Icon';

// final de Explorar: tres guías con foto y las mismas preguntas frecuentes de «Cómo funciona»
export function ShoppingGuides() {
  return (
    <>
      <section className="shopping-guides" aria-labelledby="shopping-guides-title">
        <details className="guide-disclosure">
          <summary className="guide-disclosure-heading">
            <img src="/images/products/zanahoria.webp" alt="" width="96" height="80" />
            <span><h2 id="shopping-guides-title">Compra con más idea</h2><span>Pequeñas ideas para que tu canasta rinda más.</span></span>
            <Icon name="plus" size={22} />
          </summary>
        <div className="shopping-guides-grid">
          {shoppingGuides.map((guide) => (
            <article className="shopping-guide" key={guide.id}>
              <div className="shopping-guide-visual" style={{ background: guide.tint }}>
                <img src={guide.image} alt="" loading="lazy" width="180" height="150" />
              </div>
              <div className="shopping-guide-body">
                <h3>{guide.title}</h3>
                <p>{guide.intro}</p>
                <details className="shopping-guide-details">
                  <summary>Ver consejos<span className="sr-only">: {guide.title}</span><Icon name="plus" size={18} /></summary>
                  <ul>{guide.tips.map((tip) => <li key={tip}>{tip}</li>)}</ul>
                </details>
              </div>
            </article>
          ))}
        </div>
        </details>
      </section>
      <section className="shopping-faq" aria-labelledby="shopping-faq-title">
        <div className="sec-head"><h2 id="shopping-faq-title">Preguntas frecuentes</h2></div>
        <FrequentlyAskedQuestions compact />
      </section>
    </>
  );
}

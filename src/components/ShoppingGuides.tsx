import { shoppingGuides } from '../data/shoppingGuides';
import { FrequentlyAskedQuestions } from './EditorialSections';
import './ShoppingGuides.css';

export function ShoppingGuides() {
  return (
    <>
      <section className="shopping-guides" aria-labelledby="shopping-guides-title">
        <header className="shopping-guides-heading">
          <p className="shopping-guides-kicker">Pequeñas ideas para tu semana</p>
          <h2 id="shopping-guides-title">Compra con más idea</h2>
          <p>Organiza tu canasta, entiende el ahorro y recibe tu pedido con todo claro.</p>
        </header>
        <div className="shopping-guides-grid">
          {shoppingGuides.map((guide) => (
            <article className="shopping-guide" key={guide.id}>
              <div className="shopping-guide-visual" style={{ background: guide.tint }}>
                <span>{guide.category}</span>
                <img src={guide.image} alt="" loading="lazy" width="180" height="150" />
              </div>
              <div className="shopping-guide-body">
                <h3>{guide.title}</h3>
                <p>{guide.intro}</p>
                <details className="shopping-guide-details">
                  <summary><span className="guide-open">Ver consejos</span><span className="guide-close">Cerrar consejos</span><span className="guide-summary-context">: {guide.title}</span></summary>
                  <ul>{guide.tips.map((tip) => <li key={tip}>{tip}</li>)}</ul>
                </details>
              </div>
            </article>
          ))}
        </div>
      </section>
      <section className="shopping-faq" aria-labelledby="shopping-faq-title">
        <header className="shopping-guides-heading">
          <p className="shopping-guides-kicker">Antes de confirmar</p>
          <h2 id="shopping-faq-title">Tus dudas, en claro</h2>
          <p>Lo principal sobre pedidos, pagos y entregas, sin dar tantas vueltas.</p>
        </header>
        <FrequentlyAskedQuestions />
      </section>
    </>
  );
}

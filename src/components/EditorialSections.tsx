import { Icon } from './Icon';

export function HowItWorksSection() {
  return (
      <section id="how-it-works" className="how-section" aria-labelledby="how-title">
        <div className="how-intro">
          <h2 id="how-title">Así funciona Yapa</h2>
          <p>Una compra sencilla, pensada para organizar la semana sin perder tiempo comparando precios.</p>
          <a className="secondary-button how-link" href="#catalog-title">Ver catálogo <Icon name="arrow" size={16} /></a>
        </div>
        <ol className="how-steps">
          <li>
            <span className="step-number">1</span>
            <div><h3>Arma tu canasta</h3><p>Elige lo que necesitas y mira el total mientras compras.</p></div>
          </li>
          <li>
            <span className="step-number">2</span>
            <div><h3>Reserva tu sábado</h3><p>Selecciona tu distrito, dirección y una ventana de entrega.</p></div>
          </li>
          <li>
            <span className="step-number">3</span>
            <div><h3>Recibe en tu zona</h3><p>Tu pedido llega en una sola canasta, con el medio de pago que prefieras.</p></div>
          </li>
        </ol>
      </section>
  );
}

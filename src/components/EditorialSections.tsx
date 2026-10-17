import { Icon } from './Icon';

export function HowItWorksSection() {
  return (
      <section id="how-it-works" className="how-section" aria-labelledby="how-title">
        <div className="how-intro">
          <h2 id="how-title">Así funciona Yapa</h2>
          <p>Compras junto con tus vecinos. Pagas el precio máximo y lo que ahorremos entre todos te vuelve como saldo.</p>
          <a className="secondary-button how-link" href="#catalog-title">Ver catálogo <Icon name="arrow" size={16} /></a>
        </div>
        <ol className="how-steps">
          <li>
            <span className="step-number">1</span>
            <div><h3>Arma tu canasta</h3><p>Ves el precio máximo de cada producto y hasta dónde puede bajar si entre todos pedimos más.</p></div>
          </li>
          <li>
            <span className="step-number">2</span>
            <div><h3>Paga con Yape o Plin</h3><p>Antes del miércoles a las 20:00, con el código de operación. Si tu zona no llega a 8 pedidos, te devolvemos el 100 %.</p></div>
          </li>
          <li>
            <span className="step-number">3</span>
            <div><h3>Recibe y te devolvemos</h3><p>El sábado llega a tu portería. El ahorro por volumen y lo que sobre del envío vuelven a tu saldo.</p></div>
          </li>
        </ol>
      </section>
  );
}

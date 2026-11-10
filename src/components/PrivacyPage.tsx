import { useEffect } from 'react';
import { photoCredits } from '../data/photoCredits';

// Borrador de la iteración 47 (S-252): el equipo de Yapa debe revisar el texto, sobre todo el medio de contacto y los plazos.
export function PrivacyPage() {
  useEffect(() => { document.title = 'Privacidad · Yapa'; }, []);
  return (
    <main className="invite-page">
      <article className="invite-card privacy-page">
        <div className="auth-brandline"><img src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" /><span>yapa</span></div>
        <h1>Cómo cuidamos tus datos</h1>
        <p className="privacy-draft">Versión del piloto. Este texto lo está revisando el equipo de Yapa.</p>

        <h2>Qué datos guardamos</h2>
        <ul>
          <li>Tu nombre, tu celular y tu correo.</li>
          <li>La zona donde recibes tus pedidos, tus pedidos y tu saldo a favor.</li>
          <li>Si entras con Google, solo el nombre y el correo que Google confirma. No recibimos tu contraseña de Google.</li>
          <li>Tu PIN, si creas uno. Lo guardamos cifrado: ni el equipo puede verlo.</li>
        </ul>

        <h2>Para qué los usamos</h2>
        <ul>
          <li>Armar y entregar tus pedidos, y calcular lo que ahorras.</li>
          <li>Avisarte cómo va tu pedido, en la app y, si lo permites, por correo.</li>
          <li>Ayudarte a recuperar tu cuenta si olvidas tu PIN.</li>
        </ul>

        <h2>Quién los ve</h2>
        <ul>
          <li>El equipo de Yapa.</li>
          <li>El administrador de tu zona ve tu nombre y si ya pediste esta semana, para organizar al grupo.</li>
          <li>Quien arma y entrega el pedido recibe solo lo necesario para entregarlo.</li>
        </ul>
        <p>No vendemos tus datos.</p>

        <h2>Cuánto tiempo los guardamos</h2>
        <p>Mientras uses Yapa. Si pides borrar tu cuenta, borramos tus datos, salvo lo que una norma nos obligue a conservar.</p>

        <h2>Tus derechos</h2>
        <p>Según la Ley de Protección de Datos Personales (Ley 29733), puedes pedir ver, corregir, actualizar o borrar tus datos, y oponerte a que los usemos. Escríbele al equipo de Yapa por el WhatsApp con el que te contactamos, o al administrador de tu zona, que nos hace llegar tu pedido.</p>

        <h2>Fotos de los productos</h2>
        <p>Algunas fotos del catálogo vienen de Wikimedia Commons:</p>
        <ul className="photo-credits">
          {photoCredits.map((c) => <li key={c.product}>{c.product}: <a href={c.source} target="_blank" rel="noreferrer">foto de {c.author}</a>, {c.licenseUrl ? <a href={c.licenseUrl} target="_blank" rel="noreferrer">{c.license}</a> : c.license}.</li>)}
        </ul>

        <a className="secondary-button privacy-back" href="/">Volver a Yapa</a>
      </article>
    </main>
  );
}

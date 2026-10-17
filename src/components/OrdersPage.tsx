import type { OrderRecord, OrderStatus } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';

interface OrdersPageProps {
  orders: OrderRecord[];
  onBack: () => void;
}

const statusSteps: OrderStatus[] = ['RECIBIDO', 'PREPARANDO', 'EN RUTA', 'ENTREGADO'];

function formatDate(value: string) {
  return new Intl.DateTimeFormat('es-PE', { day: 'numeric', month: 'long' }).format(new Date(value));
}

function formatWindow(code: string) {
  const labels: Record<string, string> = { SAT_09_12: '09:00 – 12:00', SAT_12_15: '12:00 – 15:00', SAT_15_18: '15:00 – 18:00' };
  return labels[code] || code;
}

function statusIndex(status: OrderStatus) {
  return statusSteps.indexOf(status);
}

export function OrdersPage({ orders, onBack }: OrdersPageProps) {
  return (
    <main className="customer-page" id="orders-page">
      <header className="customer-page-header">
        <div><span className="customer-eyebrow">Tu cuenta</span><h1>Tus pedidos, sin perder la ruta</h1><p>Aquí queda el recorrido de cada canasta: distrito, sábado y estado de entrega.</p></div>
        <div className="customer-page-note"><span className="customer-page-note-icon"><Icon name="truck" size={20} /></span><span><small>Entrega piloto</small><strong>Sábado en tu distrito</strong></span></div>
      </header>

      <div className="customer-page-grid">
        <section className="customer-main-card" aria-labelledby="orders-page-title">
          <div className="customer-section-heading"><div><span className="customer-eyebrow">Historial</span><h2 id="orders-page-title">Tus canastas</h2></div><span className="customer-count">{orders.length} {orders.length === 1 ? 'pedido' : 'pedidos'}</span></div>
          {orders.length ? <div className="orders-page-list">{orders.map((order) => { const currentStep = statusIndex(order.status); return <article className="orders-page-card" key={order.id || order.orderCode}>
            <div className="orders-page-card-top"><div><strong>{order.orderCode}</strong><span>Registrado el {formatDate(order.createdAt)}</span></div><span className="order-status">{order.status}</span></div>
            <div className="orders-page-route"><div><small>Entrega</small><strong>Sábado · {formatWindow(order.deliveryWindow)}</strong></div><div><small>Distrito</small><strong>{order.district}</strong></div><div><small>Total</small><strong>{formatMoney(order.total)}</strong></div></div>
            <ol className="order-timeline" aria-label={`Estado del pedido ${order.orderCode}`}>{statusSteps.map((step, index) => <li className={index <= currentStep ? 'is-complete' : ''} key={step}><span>{index + 1}</span><small>{step}</small></li>)}</ol>
            <p className="orders-page-address"><Icon name="pin" size={15} />{order.addressLine}{order.reference ? ` · ${order.reference}` : ''}</p>
          </article>; })}</div> : <div className="customer-empty-state"><span className="customer-empty-icon"><Icon name="box" size={27} /></span><h3>Tu primera canasta empieza aquí</h3><p>Elige productos para la semana y reserva una entrega en tu distrito.</p><button className="primary-button" type="button" onClick={onBack}>Ver catálogo <Icon name="arrow" size={17} /></button></div>}
        </section>

        <aside className="customer-side-card"><span className="customer-eyebrow">Cómo leerlo</span><h2>Tu ruta de sábado</h2><p>Yapa reúne tu compra por zona para que tengas una ventana clara y una sola entrega.</p><div className="customer-side-list"><div><span className="customer-side-number">1</span><span><strong>Recibido</strong><small>Confirmamos tu pedido.</small></span></div><div><span className="customer-side-number">2</span><span><strong>Preparando</strong><small>Armamos tu canasta.</small></span></div><div><span className="customer-side-number">3</span><span><strong>En ruta</strong><small>Va camino a tu distrito.</small></span></div></div><button className="text-button" type="button" onClick={onBack}>Seguir comprando <Icon name="arrow" size={16} /></button></aside>
      </div>
    </main>
  );
}

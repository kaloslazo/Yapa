import { useState } from 'react';
import type { OrderRecord, RefundDestination } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { windowLabel, zoneById } from '../data/catalog';
import { canCancel } from '../utils/domain';

interface OrdersPageProps {
  orders: OrderRecord[];
  balance: number;
  now: Date;
  onBack: () => void;
  onCancel: (order: OrderRecord, destination: RefundDestination) => Promise<void>;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('es-PE', { day: 'numeric', month: 'long' }).format(new Date(value));
}

export function statusLabel(order: OrderRecord) {
  if (order.status === 'REGISTRADO') return order.paymentStatus === 'VERIFICADO' ? 'Pago verificado' : 'Pago por verificar';
  return { LIQUIDADO: 'Entregado y liquidado', NO_ATENDIDO: 'Zona sin mínimo', CANCELADO: 'Cancelado', ANULADO: 'Anulado' }[order.status];
}

function methodLabel(order: OrderRecord) {
  return order.paymentMethod === 'PLIN' ? 'Plin' : 'Yape';
}

function Outcome({ order }: { order: OrderRecord }) {
  if (order.status === 'LIQUIDADO') {
    return <p className="order-outcome order-outcome--good">Costó {formatMoney(order.finalTotal ?? order.total)}. Te devolvimos <strong>{formatMoney(order.refundToBalance)}</strong> a tu saldo.</p>;
  }
  if (order.status === 'NO_ATENDIDO') {
    return <p className="order-outcome">Tu zona no llegó a 8 pedidos. Te devolvemos <strong>{formatMoney(order.refundToMethod)}</strong> a tu {methodLabel(order)}{order.refundPaidAt ? ' (ya devuelto)' : ' en un plazo de hasta 30 días'}{order.refundToBalance ? ` y ${formatMoney(order.refundToBalance)} a tu saldo` : ''}.</p>;
  }
  if (order.status === 'CANCELADO') {
    const parts = [order.refundToBalance ? `${formatMoney(order.refundToBalance)} a tu saldo` : '', order.refundToMethod ? `${formatMoney(order.refundToMethod)} a tu ${methodLabel(order)}` : ''].filter(Boolean);
    return <p className="order-outcome">{parts.length ? `Cancelado: te devolvemos ${parts.join(' y ')}.` : 'Cancelado. El equipo revisa si tu pago llegó para devolvértelo.'}</p>;
  }
  if (order.status === 'ANULADO') {
    return <p className="order-outcome">Tu pago no se verificó antes del cierre{order.refundToBalance ? `; te devolvimos ${formatMoney(order.refundToBalance)} a tu saldo` : ''}. Escríbenos si yapeaste.</p>;
  }
  return null;
}

function CancelActions({ order, onCancel }: { order: OrderRecord; onCancel: OrdersPageProps['onCancel'] }) {
  const [busy, setBusy] = useState(false);
  const run = async (destination: RefundDestination) => {
    setBusy(true);
    try {
      await onCancel(order, destination);
    } finally {
      setBusy(false);
    }
  };
  if (order.paymentStatus !== 'VERIFICADO' && order.paidExternal > 0) {
    return <div className="order-actions"><button className="secondary-button" type="button" disabled={busy} onClick={() => run('MEDIO_DE_PAGO')}>Cancelar pedido</button><small>Tu pago aún no se verificó: el equipo revisa si llegó y te lo devuelve.</small></div>;
  }
  return (
    <div className="order-actions">
      <button className="secondary-button" type="button" disabled={busy} onClick={() => run('MEDIO_DE_PAGO')}>Cancelar y devolver a mi {methodLabel(order)}</button>
      <button className="secondary-button" type="button" disabled={busy} onClick={() => run('SALDO')}>Cancelar y pasar a mi saldo</button>
    </div>
  );
}

export function OrdersPage({ orders, balance, now, onBack, onCancel }: OrdersPageProps) {
  return (
    <main className="customer-page" id="orders-page">
      <header className="customer-page-header">
        <div><span className="customer-eyebrow">Tu cuenta</span><h1>Tus pedidos, sin perder la ruta</h1><p>Lo que pagaste, lo que costó de verdad y lo que te devolvimos en cada ciclo.</p></div>
        <div className="customer-page-note"><span className="customer-page-note-icon"><Icon name="wallet" size={20} /></span><span><small>Tu saldo a favor</small><strong>{formatMoney(balance)}</strong></span></div>
      </header>

      <div className="customer-page-grid">
        <section className="customer-main-card" aria-labelledby="orders-page-title">
          <div className="customer-section-heading"><div><span className="customer-eyebrow">Historial</span><h2 id="orders-page-title">Tus canastas</h2></div><span className="customer-count">{orders.length} {orders.length === 1 ? 'pedido' : 'pedidos'}</span></div>
          {orders.length ? <div className="orders-page-list">{orders.map((order) => {
            const zone = zoneById(order.zoneId);
            const steps = [
              { label: 'Registrado', done: true },
              { label: 'Pago verificado', done: order.paymentStatus === 'VERIFICADO' || order.status === 'LIQUIDADO' || order.status === 'NO_ATENDIDO' },
              { label: order.status === 'NO_ATENDIDO' ? 'Reembolsado' : 'Liquidado', done: order.status === 'LIQUIDADO' || order.status === 'NO_ATENDIDO' },
            ];
            const closed = order.status === 'CANCELADO' || order.status === 'ANULADO';
            return <article className="orders-page-card" key={order.id || order.orderCode}>
              <div className="orders-page-card-top"><div><strong>{order.orderCode}</strong><span>Ciclo {order.cycleId || '—'} · registrado el {formatDate(order.createdAt)}</span></div><span className={`order-status order-status--${order.status.toLowerCase()}`}>{statusLabel(order)}</span></div>
              <div className="orders-page-route"><div><small>Entrega</small><strong>Sábado · {windowLabel(order.deliveryWindow)}</strong></div><div><small>Zona</small><strong>{zone?.name ?? order.district}</strong></div><div><small>Pagaste</small><strong>{formatMoney(order.total)}</strong></div></div>
              <Outcome order={order} />
              {!closed ? <ol className="order-timeline order-timeline--three" aria-label={`Estado del pedido ${order.orderCode}`}>{steps.map((step, index) => <li className={step.done ? 'is-complete' : ''} key={step.label}><span>{index + 1}</span><small>{step.label}</small></li>)}</ol> : null}
              <p className="orders-page-address"><Icon name="pin" size={15} />{zone?.name ?? order.district}{order.reference ? ` · ${order.reference}` : ''}</p>
              {canCancel(order, now) ? <CancelActions order={order} onCancel={onCancel} /> : null}
            </article>;
          })}</div> : <div className="customer-empty-state"><span className="customer-empty-icon"><Icon name="box" size={27} /></span><h3>Tu primera canasta empieza aquí</h3><p>Elige productos para la semana y paga con Yape o Plin antes del miércoles a las 20:00.</p><button className="primary-button" type="button" onClick={onBack}>Ver catálogo <Icon name="arrow" size={17} /></button></div>}
        </section>

        <aside className="customer-side-card"><span className="customer-eyebrow">Cómo funciona</span><h2>Te devolvemos</h2><p>Todos pagan el precio máximo y, cuando la compra sale mejor, la diferencia vuelve a cada vecino.</p><div className="customer-side-list"><div><span className="customer-side-number">1</span><span><strong>Pagas el máximo</strong><small>Nunca más de lo que viste al pedir.</small></span></div><div><span className="customer-side-number">2</span><span><strong>Compramos juntos</strong><small>Con más volumen baja el precio por tramo.</small></span></div><div><span className="customer-side-number">3</span><span><strong>Vuelve como saldo</strong><small>El ahorro y lo que sobre del envío, para tu próximo pedido.</small></span></div></div><button className="text-button" type="button" onClick={onBack}>Seguir comprando <Icon name="arrow" size={16} /></button></aside>
      </div>
    </main>
  );
}

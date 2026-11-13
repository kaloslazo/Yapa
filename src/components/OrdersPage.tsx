import { useState } from 'react';
import type { FormEvent } from 'react';
import type { Order, RefundDestination } from '../types';
import { Icon } from './Icon';
import { ProductThumb } from './ProductThumb';
import { PhotoPreview, usePhotoPreview } from './PhotoForm';
import { formatMoment, formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';
import { refundPromise } from '../utils/refund';
import { weekLabel } from '../utils/week';

export interface MyOrders {
  orders: Order[];
  balance: number;
  returned: number;
  supermarketSaving: number;
  refunds: Array<{ id: number; amount: number; reason: string; status: string }>;
}

export interface Claimable {
  order: number;
  product: string;
  name: string;
  quantity: number;
  until?: string; // RV-02: hasta cuándo se puede reclamar
}

export interface ClaimRecord {
  id: number;
  order: number;
  product: string;
  name?: string; // RV-03
  quantity: number;
  reason: string;
  status: string;
  returned: number;
}

interface OrdersPageProps {
  data: MyOrders | null;
  claimables: Claimable[];
  claims: ClaimRecord[];
  onBack: () => void;
  onCancel: (order: Order, destination: RefundDestination) => Promise<void>;
  onWithdraw: (amount: number) => Promise<void>;
  onClaim: (form: FormData) => Promise<void>;
}

const STATUS: Record<string, string> = {
  REGISTRADO: 'Registrado', LIQUIDADO: 'Entregado y liquidado', NO_ATENDIDO: 'Zona sin mínimo', NO_ENTREGADO: 'No se pudo entregar',
  CANCELADO_POR_CLIENTE: 'Cancelado', CANCELADO: 'Anulado', PENDIENTE: 'Pendiente', APROBADO: 'Aprobado', RECHAZADO: 'Rechazado', PAGADO: 'Pagado',
};
const REASONS: Record<string, string> = { FALTANTE: 'Faltó', DANADO: 'Llegó dañado' };
const methodName = (method: string) => (method === 'PLIN' ? 'Plin' : method === 'SALDO' ? 'saldo' : 'Yape');

export function statusLabel(order: Order) {
  if (order.status === 'REGISTRADO') return order.payment === 'VERIFICADO' ? 'Pago verificado' : 'Falta tu pago';
  return STATUS[order.status] ?? order.status;
}

function Outcome({ order }: { order: Order }) {
  const s = order.settlement;
  if (!s) return null;
  if (s.status === 'LIQUIDADO') {
    const vs = s.comparison.SUPERMERCADO;
    return (
      <div className="order-outcome order-outcome--good">
        <div className="outcome-grid"><div><small>Pagaste</small><strong>{formatMoney(s.paid)}</strong></div><div><small>Costó</small><strong>{formatMoney(s.cost)}</strong></div><div className="outcome-back"><small>Te devolvimos</small><strong>{formatMoney(s.returned)}</strong></div></div>
        {s.benefit > 0 ? <p className="outcome-line"><Icon name="crown" size={16} /> Beneficio de admin de zona: <strong>{formatMoney(s.benefit)}</strong></p> : null}
        {vs ? <p className="outcome-line outcome-line--split"><span><Icon name="tag" size={16} /> En el supermercado costaba {formatMoney(vs.before)}</span>{vs.saving >= 0 ? <strong>Ahorraste {formatMoney(vs.saving)}</strong> : <span>Pagaste {formatMoney(-vs.saving)} más</span>}</p> : null}
      </div>
    );
  }
  if (s.status === 'NO_ATENDIDO') return <p className="order-outcome">Tu grupo no llegó a 8 pedidos. Te devolvemos <strong>{formatMoney(s.returned)}</strong> (el Yape o Plin en hasta 30 días).</p>;
  if (s.status === 'NO_ENTREGADO') return <p className="order-outcome">No se pudo entregar. Te devolvimos <strong>{formatMoney(s.returned)}</strong>; solo se cobró el envío real.</p>;
  return null;
}

const TONE: Record<string, string> = { CANCELADO_POR_CLIENTE: 'muted', CANCELADO: 'muted', NO_ATENDIDO: 'warn', NO_ENTREGADO: 'warn', LIQUIDADO: 'good' };

// iteración 59: estado en una frase, pasos con hora y detalle, y las fotos del propio pedido (S-311..S-313)
function Tracking({ order }: { order: Order }) {
  if (!order.tracking?.length || !order.trackingStatus) return <Timeline order={order} />;
  const status = order.trackingStatus;
  const tone = TONE[order.status] ?? (order.payment === 'POR_VERIFICAR' ? 'pending' : 'live');
  const current = order.tracking.findIndex((s) => !s.done);
  const finished = ['CANCELADO_POR_CLIENTE', 'CANCELADO', 'NO_ATENDIDO'].includes(order.status);
  const photos = order.photos;
  return (
    <div className="tracking">
      <div className={`tracking-status tracking-status--${tone}`} role="status">
        <span className="tracking-status-icon" aria-hidden="true"><Icon name={tone === 'good' ? 'ok' : tone === 'pending' ? 'wallet' : tone === 'warn' || tone === 'muted' ? 'info' : 'truck'} size={20} /></span>
        <div><strong>{status.title}</strong>{status.detail ? <span>{status.detail}</span> : null}</div>
      </div>
      {finished ? null : <ol className="tracking-steps" aria-label={`Seguimiento del pedido ${order.id}`}>{order.tracking.map((step, index) => (
        <li key={step.step} className={step.done ? 'is-done' : index === current ? 'is-current' : ''}>
          <span className="tracking-dot" aria-hidden="true">{step.done ? <Icon name="check" size={12} weight="bold" /> : null}</span>
          <div className="tracking-text">
            <div className="tracking-head"><strong>{step.step}</strong>{step.done && step.when ? <time dateTime={step.when}>{formatMoment(step.when)}</time> : null}</div>
            {step.done && step.detail ? <p>{step.detail}</p> : index === current ? <p className="tracking-next">Siguiente paso</p> : null}
          </div>
        </li>
      ))}</ol>}
      {photos && (photos.delivery || photos.bags > 0) ? (
        <div className="tracking-photos" aria-label="Fotos de tu pedido">
          {photos.delivery ? <a href={`/api/pedidos/${order.id}/fotos/entrega`} target="_blank" rel="noopener"><img src={`/api/pedidos/${order.id}/fotos/entrega`} alt={`Foto de la entrega del pedido ${order.id}`} loading="lazy" width="72" height="72" onError={(event) => { (event.currentTarget.parentElement as HTMLElement).hidden = true; }} /><small>Entrega</small></a> : null}
          {Array.from({ length: photos.bags }, (_, i) => <a key={i} href={`/api/pedidos/${order.id}/fotos/bolsa-${i + 1}`} target="_blank" rel="noopener"><img src={`/api/pedidos/${order.id}/fotos/bolsa-${i + 1}`} alt={`Foto de la bolsa ${i + 1} del pedido ${order.id}`} loading="lazy" width="72" height="72" onError={(event) => { (event.currentTarget.parentElement as HTMLElement).hidden = true; }} /><small>Bolsa {i + 1}</small></a>)}
        </div>
      ) : null}
    </div>
  );
}

function Timeline({ order }: { order: Order }) {
  if (!['REGISTRADO', 'LIQUIDADO'].includes(order.status)) return null;
  const steps = order.tracking?.map((t) => ({ label: t.step, done: t.done })) ?? [ // S-309: el motor da los siete pasos
    { label: 'Pedido', done: true },
    { label: 'Pago verificado', done: order.payment === 'VERIFICADO' },
    { label: 'Entregado', done: order.delivered || order.status === 'LIQUIDADO' },
    { label: 'Te devolvemos', done: order.status === 'LIQUIDADO' },
  ];
  return <ol className={`order-timeline ${steps.length > 4 ? 'order-timeline--seven' : 'order-timeline--four'}`} aria-label={`Avance del pedido ${order.id}`}>{steps.map((step, index) => <li className={step.done ? 'is-complete' : ''} key={step.label}><span>{step.done ? <Icon name="check" size={13} weight="bold" /> : index + 1}</span><small>{step.label}</small></li>)}</ol>;
}

function CancelActions({ order, onCancel }: { order: Order; onCancel: OrdersPageProps['onCancel'] }) {
  const [busy, setBusy] = useState(false);
  const [asking, setAsking] = useState(false);
  const run = async (destination: RefundDestination) => {
    setBusy(true);
    try {
      await onCancel(order, destination);
    } finally {
      setBusy(false);
    }
  };
  if (!asking) return <div className="order-actions"><button className="secondary-button" type="button" onClick={() => setAsking(true)}>Cancelar pedido</button></div>;
  return (
    <div className="order-confirm" role="group" aria-label={`Cancelar el pedido ${order.id}`}>
      <p><strong>¿Cancelar el pedido {order.id}?</strong> Elige a dónde va tu dinero:</p>
      <button className="secondary-button" type="button" disabled={busy} onClick={() => void run('SALDO')}>A mi saldo<small>{refundPromise('SALDO', order.method)}</small></button>
      <button className="secondary-button" type="button" disabled={busy} onClick={() => void run('MEDIO_DE_PAGO')}>A mi {methodName(order.method)}<small>{refundPromise('MEDIO_DE_PAGO', order.method)}</small></button>
      <button className="text-button" type="button" disabled={busy} onClick={() => setAsking(false)}>No cancelar</button>
    </div>
  );
}

// S-335: se reclama tocando la tarjeta del producto; solo aparecen los de entregas de las últimas 24 horas (S-334)
function ClaimForm({ claimables, onClaim }: { claimables: Claimable[]; onClaim: OrdersPageProps['onClaim'] }) {
  const [item, setItem] = useState(0);
  const [quantity, setQuantity] = useState(1);
  const [reason, setReason] = useState('FALTANTE');
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState('');
  const { preview, choose, clear } = usePhotoPreview(); // S-336
  const chosen = claimables[item] ?? claimables[0];
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const element = event.currentTarget; // después del await React ya no conserva currentTarget
    const form = new FormData(element);
    form.set('pedido', String(chosen.order));
    form.set('producto', chosen.product);
    form.set('cantidad', String(quantity));
    form.set('motivo', reason);
    form.delete('reclamable');
    setBusy(true);
    try {
      await onClaim(form);
      setDone(`Recibimos tu reclamo por ${chosen.name}. Lo revisamos y, si corresponde, te devolvemos el monto como saldo.`);
      element.reset();
      clear();
    } finally {
      setBusy(false);
    }
  };
  if (!chosen) return <p className="admin-muted">Cuando recibas un pedido, aquí aparecen sus productos para reclamar durante 24 horas.</p>;
  return (
    <form className="claim-form" onSubmit={submit}>
      <fieldset className="claim-picks"><legend>¿Qué producto?</legend>
        {claimables.map((c, index) => (
          <label key={`${c.order}-${c.product}`} className={`claim-pick${index === item ? ' is-selected' : ''}`}>
            <input type="radio" name="reclamable" value={index} checked={index === item} onChange={() => { setItem(index); setQuantity(1); }} />
            <ProductThumb id={c.product} size={48} />
            <span><strong>{c.name}</strong><small>Pedido {c.order} · {formatQuantity(c.quantity)}{c.until ? ` · hasta ${formatMoment(c.until)}` : ''}</small></span>
          </label>
        ))}
      </fieldset>
      <div className="claim-row">
        <div className="quantity-control" aria-label="Cantidad a reclamar"><button type="button" onClick={() => setQuantity((q) => Math.max(q - 1, 1))} aria-label="Menos"><Icon name="minus" size={14} /></button><span>{quantity}</span><button type="button" onClick={() => setQuantity((q) => Math.min(q + 1, Math.ceil(chosen.quantity)))} aria-label="Más"><Icon name="plus" size={14} /></button></div>
        <div className="segmented" role="radiogroup" aria-label="Motivo">{Object.entries(REASONS).map(([value, label]) => <button key={value} type="button" role="radio" aria-checked={reason === value} className={reason === value ? 'is-active' : ''} onClick={() => setReason(value)}>{label}</button>)}</div>
      </div>
      <PhotoPreview src={preview} />
      <label className={`photo-field claim-photo-field${preview ? ' has-photo' : ''}`}><Icon name="camera" size={20} /><span>{preview ? 'Cambiar foto' : 'Tomar foto del producto'}</span><input type="file" name="foto_archivo" accept="image/*" capture="environment" required onChange={(event) => choose(event.currentTarget.files?.[0])} /></label>
      <button className="primary-button" type="submit" disabled={busy}>{busy ? 'Enviando…' : `Reclamar ${chosen.name}`}</button>
      {done ? <p className="auth-feedback auth-feedback--notice" role="status">{done}</p> : null}
    </form>
  );
}

const CLAIM_TONE: Record<string, string> = { APROBADO: 'state-pill--ok', RECHAZADO: 'state-pill--bad', PENDIENTE: '' };

function ClaimHistory({ claims }: { claims: ClaimRecord[] }) {
  if (!claims.length) return null;
  return (
    <div className="claim-history-wrap"><h3>Tus reclamos</h3>
      <ul className="claim-history">{claims.map((c) => (
        <li key={c.id}>
          <ProductThumb id={c.product} size={44} />
          <div><strong>{c.name ?? c.product} × {formatQuantity(c.quantity)}</strong><small>Pedido {c.order} · {REASONS[c.reason] ?? c.reason}</small></div>
          <div className="claim-history-state"><span className={`state-pill ${CLAIM_TONE[c.status] ?? ''}`}>{STATUS[c.status] ?? c.status}</span>{c.returned ? <small>{formatMoney(c.returned)} a tu saldo</small> : null}</div>
        </li>
      ))}</ul>
    </div>
  );
}

export function OrdersPage({ data, claimables, claims, onBack, onCancel, onWithdraw, onClaim }: OrdersPageProps) {
  const orders = data?.orders ?? [];
  const [withdrawing, setWithdrawing] = useState(false);
  const [confirmingWithdraw, setConfirmingWithdraw] = useState(false);
  const withdraw = async () => {
    if (!data?.balance) return;
    setWithdrawing(true);
    try {
      await onWithdraw(data.balance);
    } finally {
      setWithdrawing(false);
      setConfirmingWithdraw(false);
    }
  };
  return (
    <main className="customer-page" id="orders-page">
      <header className="customer-page-header savings-hero">
        <div><h1>{data && data.supermarketSaving > 0 ? <>Llevas <em>{formatMoney(data.supermarketSaving)}</em> ahorrados</> : 'Tus pedidos'}</h1><p>{data && data.supermarketSaving > 0 ? 'Frente a lo que te costaba en el supermercado. Lo que pagaste, lo que costó y lo que te devolvimos, pedido por pedido.' : 'Lo que pagaste, lo que costó de verdad y lo que te devolvimos en cada ciclo.'}</p></div>
        <div className="hero-stats">
          <div className="customer-page-note"><span className="customer-page-note-icon"><Icon name="wallet" size={20} /></span><span><small>Tu saldo a favor</small><strong>{formatMoney(data?.balance ?? 0)}</strong></span></div>
          <div className="customer-page-note"><span className="customer-page-note-icon"><Icon name="undo" size={20} /></span><span><small>Con Yapa te devolvimos</small><strong>{formatMoney(data?.returned ?? 0)}</strong></span></div>
        </div>
      </header>

      <div className="customer-page-grid">
        <section className="customer-main-card" aria-labelledby="orders-page-title">
          <div className="customer-section-heading"><div><h2 id="orders-page-title">Tus canastas</h2></div><span className="customer-count">{orders.length} {orders.length === 1 ? 'pedido' : 'pedidos'}</span></div>
          {orders.length ? <div className="orders-page-list">{orders.map((order) => (
            <article className="orders-page-card" key={order.id}>
              <div className="orders-page-card-top"><div><strong>Pedido {order.id}</strong><span>{weekLabel(order.cycle)}</span></div><span className={`order-status order-status--${order.status === 'REGISTRADO' ? order.payment.toLowerCase() : order.status.toLowerCase()}`}>{statusLabel(order)}</span></div>
              {order.status === 'REGISTRADO' && order.payment === 'POR_VERIFICAR' && order.toPay > 0 ? <div className="pay-reminder"><Icon name="wallet" size={18} /><span>Paga <strong>{formatMoney(order.toPay)}</strong>{order.payTo ? <> al Plin <strong>{order.payTo.number}</strong> ({order.payTo.holder})</> : <> por {methodName(order.method)}</>} con el código <code>{order.paymentCode}</code> en el mensaje. También puedes pagar desde Yape.</span></div> : null}
              <Tracking order={order} />
              <Outcome order={order} />
              <details className="order-lines"><summary>{order.lines.length} productos · {formatMoney(order.total)}</summary><ul className="order-cart">{order.lines.map((line) => <li key={line.id}><ProductThumb id={line.id} size={48} /><div><strong>{line.name}</strong><small>{formatQuantity(line.quantity)} · hasta {formatMoney(line.maxPrice)} c/u</small></div><strong className="order-cart-total">{formatMoney(line.total)}</strong></li>)}</ul></details>
              {order.cancellable ? <CancelActions order={order} onCancel={onCancel} /> : null}
            </article>
          ))}</div> : <div className="customer-empty-state"><span className="customer-empty-icon"><Icon name="basket" size={27} /></span><h3>Tu primera canasta empieza aquí</h3><p>Elige productos para la semana y paga con Yape o Plin antes del miércoles a las 20:00.</p><button className="primary-button" type="button" onClick={onBack}>Ver catálogo <Icon name="arrow" size={17} /></button></div>}
        </section>

        <aside className="customer-side-stack">
          <section className="customer-side-card">
            <h2>{formatMoney(data?.balance ?? 0)}</h2>
            <p>Se usa solo en tu próximo pedido. No vence. Si lo prefieres, te lo devolvemos a tu Yape o Plin en hasta 30 días.</p>
            {confirmingWithdraw ? <div className="order-confirm" role="group" aria-label="Confirmar devolución del saldo"><p><strong>¿Devolverte {formatMoney(data?.balance ?? 0)} a tu Yape o Plin?</strong> Te lo devolvemos en hasta 30 días.</p><button className="primary-button" type="button" disabled={withdrawing} onClick={() => void withdraw()}>{withdrawing ? 'Enviando…' : 'Sí, devolverme'}</button><button className="text-button" type="button" disabled={withdrawing} onClick={() => setConfirmingWithdraw(false)}>No, dejarlo en mi saldo</button></div>
              : <button className="secondary-button" type="button" disabled={!data?.balance} onClick={() => setConfirmingWithdraw(true)}>Devolverme todo a mi Yape/Plin</button>}
            {data?.refunds.length ? <table className="mini-table"><caption>Devoluciones en curso</caption><tbody>{data.refunds.map((r) => <tr key={r.id}><td>{formatMoney(r.amount)}</td><td>{STATUS[r.status] ?? r.status}</td></tr>)}</tbody></table> : null}
          </section>
          <section className="customer-side-card">
            <span className="customer-eyebrow">¿Algo faltó o llegó mal?</span><h2>Reclamos</h2>
            <ClaimForm claimables={claimables} onClaim={onClaim} />
            <ClaimHistory claims={claims} />
          </section>
        </aside>
      </div>
    </main>
  );
}

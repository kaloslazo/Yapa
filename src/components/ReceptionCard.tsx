import { ConfirmAction } from './ConfirmAction';
import { Icon } from './Icon';
import { RECEPTION_LABELS } from '../utils/receptionUpdates';

/* eslint-disable @typescript-eslint/no-explicit-any */
type Raw = Record<string, any>;

// iteración 55: lo que llegó a un edificio; la usan la portería y el admin de zona (PO-01, S-293)
const STATES: Record<string, { label: string; note: string }> = {
  pendiente: { label: 'Por llegar', note: 'El reparto llega el sábado. Cuando entregue, aquí ves las bolsas y de quién son.' },
  entregada: { label: 'Por confirmar', note: 'El reparto ya dejó las bolsas. Revisa que estén todas y confirma: cada vecino recibe un aviso para bajar a recogerlas.' },
  recibida: { label: 'Recibida', note: 'Ya confirmaste. Los vecinos saben que sus bolsas están en el edificio.' },
  fallida: { label: 'No se entregó', note: 'El reparto no pudo dejar las bolsas esta semana. Yapa devuelve el dinero a cada vecino.' },
};

const time = (iso: string) => new Date(iso).toLocaleString('es-PE', { timeZone: 'America/Lima', weekday: 'short', day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' });

export function ReceptionCard({ data, onConfirm }: { data: Raw; onConfirm: () => Promise<unknown> }) {
  const state = STATES[data.estado] ?? STATES.pendiente;
  const orders: Raw[] = data.pedidos;
  const bags = orders.reduce((sum, o) => sum + o.bolsas, 0);
  return (
    <article className={`route-stop reception-card route-stop--${data.estado === 'recibida' ? 'entregada' : data.estado}`}>
      <div className="route-stop-head">
        <span className="route-stop-number" aria-hidden="true"><Icon name={data.estado === 'recibida' ? 'check' : 'building'} size={17} /></span>
        <div><h2>{data.zona.nombre}</h2><p>{data.zona.distrito}</p></div>
        <span className={`route-state reception-state--${data.estado}`}>{RECEPTION_LABELS[data.seguimiento] ?? state.label}</span>
      </div>
      <p className="partner-muted">{data.seguimiento === 'sin_pedidos' ? 'Todavía no hay pedidos para recibir en esta semana.' : data.seguimiento === 'preparando' ? 'Los pedidos están en preparación. Aquí verás cuándo las bolsas estén listas para despacho.' : data.seguimiento === 'en_camino' ? 'El reparto salió hacia tu edificio. Te avisamos aquí cuando registre la llegada.' : data.seguimiento === 'listo' ? 'Las bolsas están listas para despacho. El reparto todavía no ha registrado su salida.' : state.note}</p>
      {data.seguimiento && data.seguimiento !== 'sin_pedidos' ? <div className="reception-progress" aria-label="Seguimiento de la entrega">
        <ol>{['preparando', 'listo', 'en_camino', 'entregada', 'recibida'].map((step, i, all) => {
          const reached = (step === 'preparando' && orders.length > 0) || (data.hitos ?? []).some((h: Raw) => h.estado === step) || step === data.seguimiento;
          return <li key={step} className={reached ? 'is-done' : ''} aria-current={data.seguimiento === step ? 'step' : undefined}><span>{reached ? <Icon name="check" size={13} /> : i + 1}</span>{RECEPTION_LABELS[step]}{i < all.length - 1 ? <span className="sr-only">, después </span> : null}</li>;
        })}</ol>
        {data.hitos?.length ? <details><summary>Ver cambios de estado</summary><ul>{data.hitos.map((h: Raw) => <li key={`${h.estado}:${h.hora}`}><strong>{RECEPTION_LABELS[h.estado]}</strong><time dateTime={h.hora}>{time(h.hora)}</time></li>)}</ul></details> : null}
      </div> : null}
      <dl className="route-facts">
        <div><dt>Llegan</dt><dd>{bags} {bags === 1 ? 'bolsa' : 'bolsas'} · {orders.length} {orders.length === 1 ? 'pedido' : 'pedidos'}</dd></div>
        <div><dt>{data.confirmo ? 'Confirmado' : 'Entregó el reparto'}</dt><dd>{data.confirmo ? time(data.confirmo.hora) : data.entrego ? time(data.entrego.hora) : '—'}</dd></div>
      </dl>
      {orders.length ? <ul className="reception-list" aria-label="Bolsas por vecino">{orders.map((o) => (
        <li key={o.id}><span className="reception-name">{o.vecino}</span><span className="reception-order">Pedido {o.id}</span><span className="reception-bags"><Icon name="box" size={15} />{o.bolsas} {o.bolsas === 1 ? 'bolsa' : 'bolsas'}</span></li>
      ))}</ul> : <p className="partner-muted">Esta semana no hay pedidos para este edificio.</p>}
      {data.estado === 'entregada' ? <div className="route-actions"><ConfirmAction label={<><Icon name="check" size={18} /> Confirmar que recibí {bags} {bags === 1 ? 'bolsa' : 'bolsas'}</>} question="¿Están todas? Avisaremos a cada vecino." confirmLabel="Sí, confirmar" onConfirm={onConfirm} /></div> : null}
    </article>
  );
}

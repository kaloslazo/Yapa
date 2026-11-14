import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import type { Account } from '../types';
import { PhotoProductReview } from './PhotoProductReview';
import { formatMoney, quantityWithUnit } from '../utils/format';
import { weekLabel } from '../utils/week';
import { Icon } from './Icon';
import { PhotoForm } from './PhotoForm';
import { ProductThumb } from './ProductThumb';
import { ReceptionCard } from './ReceptionCard';
import { PartnerSkeleton } from './Skeleton';
import { SupplierListEditor } from './SupplierListEditor';
import { RoutePlanner } from './RoutePlanner';
import { orderDelivery } from '../utils/deliveryRoute';
import { RECEPTION_LABELS, unseenReceptionEvents, type ReceptionSnapshot } from '../utils/receptionUpdates';

/* eslint-disable @typescript-eslint/no-explicit-any */
type Raw = Record<string, any>;
type Notify = (message: string, tone?: 'neutral' | 'success' | 'warning', detail?: string) => void;

// iteraciones 54 y 55: el transportista, el proveedor y la portería tienen su propia pantalla, sin tienda ni panel del equipo
interface PartnerPanelProps {
  account: Account;
  notify: Notify;
  onLogout: () => void;
}

const RECEIVERS: Record<string, string> = { PORTERIA: 'Portería', ENCARGADO: 'Encargado', ADMIN: 'Admin de zona' };
const FAILURES = [{ value: 'PORTERIA_CERRADA', label: 'Portería cerrada' }, { value: 'NADIE_RECIBE', label: 'No había quién reciba' }, { value: 'PORTERIA_RECHAZA', label: 'No aceptaron' }];
const OFFER_STATES: Record<string, string> = { PENDIENTE: 'En revisión', APROBADA: 'Aprobada', RECHAZADA: 'Rechazada' };

function useData(path: string, notify: Notify) {
  const [data, setData] = useState<Raw | null>(null);
  const reload = useCallback(async () => {
    try {
      setData(await api.get<Raw>(path));
    } catch (error) {
      notify('No pudimos cargar tus datos', 'warning', error instanceof Error ? error.message : undefined);
    }
  }, [path, notify]);
  useEffect(() => { void reload(); }, [reload]);
  return { data, reload };
}

function WeekSelect({ cycles, value, onChange }: { cycles: string[]; value: string; onChange: (cycle: string) => void }) {
  return <label className="partner-week"><span className="sr-only">Semana</span><select value={value} onChange={(event) => onChange(event.target.value)}>{cycles.map((c) => <option key={c} value={c}>{weekLabel(c)}</option>)}</select></label>;
}

const SCREENS: Record<string, string> = { transportista: 'reparto', proveedor: 'proveedores', porteria: 'portería' };

export function PartnerPanel({ account, notify, onLogout }: PartnerPanelProps) {
  return (
    <div className="partner-view">
      <header className="partner-topbar">
        <div className="partner-brand"><img src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" /><span>yapa</span><small>{SCREENS[account.role]}</small></div>
        <button className="partner-logout" type="button" onClick={onLogout}><Icon name="signout" size={18} />Salir</button>
      </header>
      <main className="partner-main" id="contenido">
        {account.role === 'transportista' ? <DriverRoute name={account.name} notify={notify} /> : account.role === 'porteria' ? <ConciergeHome name={account.name} notify={notify} /> : <SupplierHome notify={notify} />}
      </main>
    </div>
  );
}

function DriverRoute({ name, notify }: { name: string; notify: Notify }) {
  const [cycle, setCycle] = useState('');
  const [routeIds, setRouteIds] = useState<string[] | null>(null);
  useEffect(() => setRouteIds(null), [cycle]);
  const { data, reload } = useData(`/api/reparto${cycle ? `?ciclo=${cycle}` : ''}`, notify);
  const [failure, setFailure] = useState('PORTERIA_CERRADA');
  if (!data) return <PartnerSkeleton />;
  const stops: Raw[] = orderDelivery(data.paradas, routeIds);
  const done = stops.filter((s) => s.estado === 'entregada' || s.estado === 'fallida').length;
  const send = async (path: string, form: FormData, extra: Record<string, string>, title: string, detail: string) => {
    for (const [key, value] of Object.entries(extra)) form.set(key, value);
    try {
      await api.post(path, form);
      notify(title, 'success', detail);
      await reload();
      return true;
    } catch (error) {
      notify('No se pudo registrar', 'warning', error instanceof Error ? error.message : undefined);
      return false;
    }
  };
  return (
    <>
      <section className="partner-head">
        <h1>Hola, {name.split(' ')[0]}</h1>
        <WeekSelect cycles={data.ciclos} value={data.ciclo} onChange={setCycle} />
        {stops.length ? <p className="partner-progress"><strong>{done} de {stops.length}</strong> paradas listas</p> : null}
      </section>
      {!data.cerrado && stops.length ? <p className="partner-note"><Icon name="calendar" size={18} />Los pedidos cierran el miércoles a las 8 p. m. Las paradas pueden cambiar hasta entonces.</p> : null}
      {stops.length ? <RoutePlanner key={data.ciclo} stops={data.paradas} active={Boolean(routeIds)} onOrder={setRouteIds} /> : null}
      {stops.length ? <ol className="stop-route">{stops.map((stop, index) => {
        const zone = stop.zona;
        const unpacked = stop.pedidos.filter((o: Raw) => o.bolsas === 0).length;
        const bags = stop.pedidos.reduce((sum: number, o: Raw) => sum + o.bolsas, 0);
        return (
          <li key={zone.id} className={`route-stop route-stop--${stop.estado}`}>
            <div className="route-stop-head">
              <span className="route-stop-number" aria-hidden="true">{stop.estado === 'entregada' ? <Icon name="check" size={16} /> : index + 1}</span>
              <div><h2>{zone.nombre}</h2><p>{zone.distrito}</p></div>
              <span className={`route-state route-state--${stop.estado}`}>{stop.estado === 'entregada' ? 'Entregada' : stop.estado === 'fallida' ? 'No se pudo' : stop.estado === 'en_camino' ? 'En camino' : 'Pendiente'}</span>
            </div>
            <dl className="route-facts">
              <div><dt>Recibe</dt><dd>{zone.contacto || RECEIVERS[zone.recibe] || 'Recepción'}</dd></div>
              <div><dt>Lleva</dt><dd>{bags} {bags === 1 ? 'bolsa' : 'bolsas'} de {stop.pedidos.length} {stop.pedidos.length === 1 ? 'pedido' : 'pedidos'}</dd></div>
            </dl>
            <ul className="route-orders" aria-label="Pedidos de la parada">{stop.pedidos.map((o: Raw) => <li key={o.id} className={o.bolsas ? '' : 'is-missing'}>N.º {o.id}<span>{o.bolsas ? `${o.bolsas} ${o.bolsas === 1 ? 'bolsa' : 'bolsas'}` : 'sin armar'}</span></li>)}</ul>
            {zone.lat != null && zone.lon != null ? <a className="route-map" href={`https://www.google.com/maps/dir/?api=1&destination=${zone.lat},${zone.lon}`} target="_blank" rel="noreferrer"><Icon name="map" size={17} />Cómo llegar</a> : null}
            {stop.estado === 'pendiente' || stop.estado === 'en_camino' ? (unpacked ? <p className="partner-note partner-note--warn"><Icon name="warning" size={18} />Faltan armar {unpacked} {unpacked === 1 ? 'pedido' : 'pedidos'}. Avisa al equipo antes de salir.</p> : (
              <div className="route-actions">
                {stop.estado === 'pendiente' ? <button className="secondary-button" type="button" onClick={() => void send('/api/reparto/salidas', new FormData(), { ciclo: data.ciclo, zona: zone.id }, `Saliste hacia ${zone.nombre}`, 'Cada vecino recibe el aviso de que su pedido va en camino.')}><Icon name="truck" size={17} />Salí hacia esta zona</button> : null}
                <PhotoForm big label="Entregué" onSend={(form) => send('/api/reparto/entregas', form, { ciclo: data.ciclo, zona: zone.id }, `Entrega en ${zone.nombre} registrada`, 'Los vecinos reciben el aviso con tu foto.')}>
                  <label className="checkout-field"><span>¿Quién recibió?</span><input name="recibe" defaultValue={zone.contacto} autoComplete="off" required /></label>
                </PhotoForm>
                <details className="route-failed"><summary>No pude entregar</summary>
                  <div className="segmented" role="radiogroup" aria-label="Motivo">{FAILURES.map((f) => <label key={f.value} className={failure === f.value ? 'is-selected' : ''}><input type="radio" name={`motivo-${zone.id}`} value={f.value} checked={failure === f.value} onChange={() => setFailure(f.value)} />{f.label}</label>)}</div>
                  <PhotoForm label="Registrar que no se pudo" onSend={(form) => send('/api/reparto/entregas-fallidas', form, { ciclo: data.ciclo, zona: zone.id, motivo: failure }, `Registramos lo que pasó en ${zone.nombre}`, 'El equipo devuelve el dinero de esa zona; no tienes que volver.')} />
                </details>
              </div>
            )) : stop.recibio ? <p className="partner-muted">Recibió {stop.recibio}.</p> : null}
          </li>
        );
      })}</ol> : <div className="partner-empty"><Icon name="truck" size={26} /><strong>{data.cerrado ? 'No hay paradas esta semana' : 'Todavía no hay paradas'}</strong><p>{data.cerrado ? 'Ningún grupo llegó al mínimo de pedidos.' : 'Aparecen cuando cierran los pedidos, el miércoles a las 8 p. m.'}</p></div>}
    </>
  );
}

// iteración 55, PO-01..PO-04: la portería ve las bolsas de su edificio y confirma que llegaron
function ConciergeHome({ name, notify }: { name: string; notify: Notify }) {
  const [cycle, setCycle] = useState('');
  const [data, setData] = useState<Raw | null>(null);
  const [status, setStatus] = useState('todos');
  const [offline, setOffline] = useState(false);
  const notificationQueue = useRef<string[]>([]);
  const previous = useRef<ReceptionSnapshot | null>(null);
  const currentReload = useRef<() => Promise<void>>(async () => {});
  useEffect(() => {
    let active = true, loading = false;
    previous.current = null;
    notificationQueue.current = [];
    setData(null);
    setStatus('todos');
    const refresh = async () => {
      if (loading) return;
      loading = true;
      try {
        const next = await api.get<Raw>(`/api/porteria${cycle ? `?ciclo=${cycle}` : ''}`);
        if (!active) return;
        const updates = unseenReceptionEvents(previous.current, next as ReceptionSnapshot);
        notificationQueue.current.push(...updates.map(event => `${next.zona.nombre}: ${RECEPTION_LABELS[event.estado] ?? event.estado}`));
        if (notificationQueue.current.length) notify(notificationQueue.current.shift()!, 'success');
        previous.current = next as ReceptionSnapshot;
        setData(next);
        setOffline(false);
      } catch { if (active) setOffline(true); }
      finally { loading = false; }
    };
    currentReload.current = refresh;
    void refresh();
    const timer = window.setInterval(() => { if (!document.hidden) void refresh(); }, 15_000);
    const notificationTimer = window.setInterval(() => {
      if (!document.hidden && notificationQueue.current.length) notify(notificationQueue.current.shift()!, 'success');
    }, 6_000);
    const visible = () => { if (!document.hidden) void refresh(); };
    document.addEventListener('visibilitychange', visible);
    return () => { active = false; window.clearInterval(timer); window.clearInterval(notificationTimer); notificationQueue.current = []; document.removeEventListener('visibilitychange', visible); };
  }, [cycle, notify]);
  const reload = () => currentReload.current();
  if (!data && offline) return <div className="partner-card" role="alert"><p>No pudimos conectar con tu portería.</p><button className="secondary-button" onClick={() => void reload()}>Reintentar</button></div>;
  if (!data) return <PartnerSkeleton />;
  const confirm = async () => {
    try {
      await api.post('/api/porteria/recepciones', { ciclo: data.ciclo });
      await reload();
    } catch (error) {
      notify('No se pudo confirmar', 'warning', error instanceof Error ? error.message : undefined);
    }
  };
  return (
    <>
      <section className="partner-head">
        <h1>Hola, {name.split(' ')[0]}</h1>
        <p className="partner-building"><Icon name="building" size={18} />{data.zona.nombre}</p>
        <WeekSelect cycles={data.ciclos} value={data.ciclo} onChange={setCycle} />
      </section>
      <div className="concierge-filters">
        <label className="checkout-field"><span>Filtrar por estado</span><select value={status} onChange={e => setStatus(e.target.value)}><option value="todos">Todos los estados</option>{Object.entries(RECEPTION_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <button className="secondary-button" type="button" onClick={() => void reload()}>Actualizar</button>
      </div>
      <p className="partner-muted" role="status">{offline ? 'Sin conexión. Mostramos el último estado recibido; reintentaremos automáticamente.' : 'Actualización automática cada 15 segundos. Los cambios aparecen como avisos en esta página.'}</p>
      {status === 'todos' || status === data.seguimiento ? <ReceptionCard data={data} onConfirm={confirm} /> : <div className="partner-card"><p>No hay entregas de tu zona con ese estado en esta semana.</p><button className="text-button" type="button" onClick={() => setStatus('todos')}>Ver todos los estados</button></div>}
      <p className="partner-note"><Icon name="info" size={18} />Solo ves el nombre de cada vecino y cuántas bolsas lleva. Lo que compró y lo que pagó es privado.</p>
    </>
  );
}

function SupplierHome({ notify }: { notify: Notify }) {
  const [cycle, setCycle] = useState('');
  const { data, reload } = useData(`/api/proveedor${cycle ? `?ciclo=${cycle}` : ''}`, notify);
  const [busy, setBusy] = useState(false);
  if (!data) return <PartnerSkeleton />;
  const order = data.pedido;
  const next: Raw | undefined = data.propuestas.find((o: Raw) => o.ciclo === data.proximo);
  const text = next?.lista ?? data.lista_actual;
  const submit = async (text: string) => {
    setBusy(true);
    try {
      await api.post('/api/proveedor/propuestas', { ciclo: data.proximo, lista: text });
      notify('Lista enviada', 'success', 'El equipo de Yapa la revisa antes de publicarla. Te avisamos aquí mismo.');
      await reload();
      return true;
    } catch (error) {
      notify('No pudimos recibir tu lista', 'warning', error instanceof Error ? error.message : undefined);
      return false;
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <section className="partner-head">
        <h1>{data.proveedor.nombre}</h1>
        <WeekSelect cycles={data.ciclos} value={order.ciclo} onChange={setCycle} />
      </section>
      <section className="partner-card" aria-labelledby="pedido-title">
        <h2 id="pedido-title">Lo que te compramos</h2>
        {order.parcial ? <p className="partner-note"><Icon name="calendar" size={18} />Parcial: los pedidos cierran el miércoles a las 8 p. m.</p> : null}
        {order.lineas.length ? <>
          <ul className="supplier-lines">{order.lineas.map((line: Raw) => (
            <li key={line.producto}>
              <ProductThumb id={line.producto} size={44} />
              <div><strong>{line.nombre}</strong><span>{formatMoney(Number(line.precio))} por {line.unidad}{line.desde !== '0' ? ` · precio desde ${line.desde} ${line.unidad}` : ''}</span></div>
              <div className="supplier-line-amount"><strong>{quantityWithUnit(line.cantidad, line.unidad)}</strong><span>{formatMoney(Number(line.monto))}</span></div>
            </li>
          ))}</ul>
          <p className="supplier-total"><span>Total a tu precio</span><strong>{formatMoney(Number(order.total))}</strong></p>
        </> : <p className="partner-muted">Todavía no hay pedidos de tus productos en esta semana.</p>}
      </section>
      <PhotoProductReview key={data.proximo} />
      <section className="partner-card" aria-labelledby="lista-title">
        <h2 id="lista-title">Tu lista para la {weekLabel(data.proximo)}</h2>
        {next ? <p className={`offer-state offer-state--${next.estado.toLowerCase()}`}>{OFFER_STATES[next.estado]}{next.motivo ? `: ${next.motivo}` : ''}</p> : null}
        <SupplierListEditor key={data.proximo} initialText={text} busy={busy} resubmit={Boolean(next)} onSubmit={submit} />
      </section>
    </>
  );
}

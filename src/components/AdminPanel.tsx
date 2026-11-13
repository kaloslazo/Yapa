import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { api } from '../services/api';
import { toOrder, toZone } from '../services/mappers';
import type { Order, Role, Zone } from '../types';
import { Icon, type IconName } from './Icon';
import { statusLabel } from './OrdersPage';
import { amountWithUnit, formatMoney, quantityWithUnit } from '../utils/format';
import { formatQuantity } from '../utils/cart';
import { claimEffect, filterNeighbors, photoUrl } from '../utils/admin';
import { ConfirmAction } from './ConfirmAction';
import { PhotoForm } from './PhotoForm';
import { ProductThumb } from './ProductThumb';
import { AdminSkeleton } from './Skeleton';
import type { MapUnion, MapZone } from './ZonesMap';
import { LazyZonesMap } from './LazyZonesMap';
import { drawableZones, groupColors, marginLabel, unionLabel } from '../utils/zoneMap';
import { groupsOf, sectionsFor, type Section } from '../utils/adminSections';
import { ROLE_LABELS } from '../utils/roles';
import { humanizeWeeks, shortDate, weekRangeLabel } from '../utils/week';

/* eslint-disable @typescript-eslint/no-explicit-any */
type Raw = Record<string, any>;

interface AdminPanelProps {
  adminName: string;
  role: Role;
  onClose?: () => void; // solo el admin vuelve a la tienda; compras, armado y atención no compran

  onLogout: () => void;
  onViewAs?: (customerId: number) => Promise<void>;
  notify: (message: string, tone?: 'neutral' | 'success' | 'warning') => void;
}

const PENDING_NOUN: Partial<Record<Section, string>> = { zonas: 'propuestas', vecinos: 'solicitudes de PIN', pines: 'solicitudes de PIN', cuentas: 'listas por revisar' };
// iteración 55: contadores de la barra lateral; cada rol pide solo los de sus secciones
const PENDING: Partial<Record<Section, (cycle: string) => Promise<number>>> = {
  resumen: async (cycle) => num((await api.get<Raw>(`/api/admin/resumen${cycle ? `?ciclo=${cycle}` : ''}`)).indicadores.por_verificar),
  reclamos: async () => (await api.get<Raw>('/api/admin/reclamos')).reclamos.filter((c: Raw) => c.estado === 'PENDIENTE').length,
  devoluciones: async () => (await api.get<Raw>('/api/admin/devoluciones')).devoluciones.length,
  zonas: async (cycle) => (await api.get<Raw>(`/api/admin/analisis${cycle ? `?ciclo=${cycle}` : ''}`)).propuestas.length,
  vecinos: async () => (await api.get<Raw>('/api/admin/pin-solicitudes')).solicitudes.length,
  pines: async () => (await api.get<Raw>('/api/admin/pin-solicitudes')).solicitudes.length,
  cuentas: async () => (await api.get<Raw>('/api/admin/propuestas')).propuestas.filter((o: Raw) => o.estado === 'PENDIENTE').length,
};
const num = (value: unknown) => Number(value ?? 0);
const CLAIM_STATUS: Record<string, string> = { APROBADO: 'Aprobado', RECHAZADO: 'Rechazado', PENDIENTE: 'Pendiente' };
const REASONS: Record<string, string> = { FALTANTE: 'Faltó', DANADO: 'Llegó dañado', ZONA_NO_ATENDIDA: 'Su grupo no llegó al mínimo', CANCELACION: 'Cancelación', CANCELACION_CLIENTE: 'Canceló su pedido', RETIRO_SALDO: 'Pidió su saldo', SOLICITUD_CLIENTE: 'Pidió su saldo', NO_ENTREGADO: 'No se pudo entregar' };
const AI_CATEGORIES: Record<string, string> = { FALTANTE: 'Faltante', DANADO: 'Dañado', ENTREGA: 'Entrega', PAGO: 'Pago', TRATO: 'Trato', OTRO: 'Otro' };
const INCIDENT_KINDS = [{ value: 'ENTREGA', label: 'Entrega' }, { value: 'BOLSA', label: 'Bolsa' }, { value: 'TRATO', label: 'Trato' }, { value: 'OTRO', label: 'Otro' }]; // S-300
const FAILURES = [{ value: 'PORTERIA_CERRADA', label: 'Portería cerrada' }, { value: 'NADIE_RECIBE', label: 'No había quién reciba' }, { value: 'PORTERIA_RECHAZA', label: 'La portería no aceptó' }];

function useLoad<T>(path: string | null, notify: AdminPanelProps['notify']) {
  const [data, setData] = useState<T | null>(null);
  const reload = useCallback(async () => {
    if (!path) return;
    try {
      setData(await api.get<T>(path));
    } catch (error) {
      notify(error instanceof Error ? error.message : 'No pudimos cargar los datos.', 'warning');
    }
  }, [path, notify]);
  useEffect(() => { void reload(); }, [reload]);
  return { data, reload };
}

function Card({ eyebrow, title, children, aside, id }: { eyebrow?: string; title: string; children: ReactNode; aside?: ReactNode; id?: string }) {
  return <section className="admin-card" id={id}><div className="admin-card-heading"><div>{eyebrow ? <span className="admin-eyebrow">{eyebrow}</span> : null}<h2>{title}</h2></div>{aside}</div>{children}</section>;
}

// S-328: la semana se ve por sus fechas; el código ISO solo viaja a la API
function CycleSelect({ cycles, value, onChange }: { cycles: string[]; value: string; onChange: (cycle: string) => void; dates?: boolean }) {
  return <label className="admin-filter admin-filter--dates"><span className="sr-only">Semana</span><select value={value} onChange={(event) => onChange(event.target.value)}>{cycles.map((c) => <option key={c} value={c}>{weekRangeLabel(c)}</option>)}</select></label>;
}

// S-327: en el celular cada fila es una tarjeta; cada celda lleva el nombre de su columna
function labelTables(root: HTMLElement) {
  for (const table of root.querySelectorAll<HTMLTableElement>('table.admin-table')) {
    const heads = [...table.querySelectorAll('thead th')].map((th) => th.textContent?.trim() || 'Acciones');
    if (!heads.length) continue;
    for (const row of table.querySelectorAll('tbody tr')) [...row.children].forEach((cell, i) => { if (cell.getAttribute('data-label') !== heads[i]) cell.setAttribute('data-label', heads[i] ?? ''); });
  }
}

function Empty({ icon, title, text }: { icon: IconName; title: string; text: string }) {
  return <div className="admin-orders-empty"><span className="admin-empty-icon"><Icon name={icon} size={23} /></span><div><strong>{title}</strong><p>{text}</p></div></div>;
}

export function AdminPanel({ adminName, role, onClose, onLogout, onViewAs, notify }: AdminPanelProps) {
  const sections = useMemo(() => sectionsFor(role), [role]);
  const [section, setSection] = useState<Section>(sections[0]?.id ?? 'resumen');
  const [cycle, setCycle] = useState('');
  const [pending, setPending] = useState<Partial<Record<Section, number>>>({});

  const refreshPending = useCallback(async () => {
    try {
      const counted = sections.filter((s) => PENDING[s.id]);
      const counts = await Promise.all(counted.map((s) => PENDING[s.id]!(cycle)));
      setPending(Object.fromEntries(counted.map((s, i) => [s.id, counts[i]])));
    } catch {
      setPending({});
    }
  }, [cycle, sections]);
  useEffect(() => { void refreshPending(); }, [refreshPending, section]);

  useEffect(() => { window.scrollTo({ top: 0, behavior: 'auto' }); }, [section]);

  const run = useCallback(async (action: () => Promise<unknown>, success: string) => {
    try {
      await action();
      notify(success, 'success');
      void refreshPending();
      return true;
    } catch (error) {
      notify(error instanceof Error ? error.message : 'No se pudo completar.', 'warning');
      return false;
    }
  }, [notify, refreshPending]);

  const content = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const root = content.current;
    if (!root) return;
    labelTables(root);
    const observer = new MutationObserver(() => labelTables(root));
    observer.observe(root, { childList: true, subtree: true });
    return () => observer.disconnect();
  }, []);

  const current = sections.find((s) => s.id === section) ?? sections[0];
  const props = { cycle, setCycle, run, notify, onViewAs, role };
  const roleLabel = role === 'admin' ? 'Equipo de operaciones' : ROLE_LABELS[role];

  return (
    <div className="admin-view">
      <div className="admin-shell">
        <aside className="admin-sidebar" aria-label="Navegación de operaciones">
          <a className="admin-brand" href="#admin" aria-label="Yapa, centro de operaciones" onClick={(event) => { event.preventDefault(); setSection(sections[0].id); }}>
            <img src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" />
            <span><strong>yapa</strong><small>operaciones</small></span>
          </a>
          <nav className="admin-nav" aria-label="Secciones del panel">
            {groupsOf(sections).map((group) => <div className="admin-nav-group" key={group}><span className="admin-sidebar-label">{group}</span>{sections.filter((s) => s.group === group).map((s) => <button key={s.id} type="button" className={`admin-nav-link ${section === s.id ? 'is-active' : ''}`} aria-current={section === s.id ? 'page' : undefined} onClick={(event) => { setSection(s.id); event.currentTarget.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' }); }}><Icon name={s.icon} size={18} /><span>{s.label}</span>{pending[s.id] ? <strong>{pending[s.id]}<span className="sr-only"> {PENDING_NOUN[s.id] ?? 'pendientes'}</span></strong> : null}</button>)}</div>)}
          </nav>
          <div className="admin-sidebar-footer">
            <div className="admin-sidebar-user"><span className="admin-avatar" aria-hidden="true">{adminName.trim().charAt(0).toUpperCase() || 'Y'}</span><span><strong>{adminName}</strong><small>{roleLabel}</small></span></div>
            <div className="admin-sidebar-actions">
              {onClose ? <a className="admin-footer-button" href="#catalog" onClick={(event) => { event.preventDefault(); onClose(); }}><Icon name="store" size={16} />Tienda</a> : null}
              <button className="admin-footer-button" type="button" onClick={onLogout}><Icon name="signout" size={16} />Salir</button>
            </div>
          </div>
        </aside>

        <main className="admin-main" id="admin-overview">
          <header className="admin-topbar">
            <span className="admin-topbar-icon" aria-hidden="true"><Icon name={current.icon} size={22} /></span>
            <div><span className="admin-topbar-group">{current.group}</span><h1>{current.label}</h1><p>{current.hint}</p></div>
          </header>
          <div className="admin-page-content" ref={content}>
            {section === 'resumen' ? <Summary {...props} /> : null}
            {section === 'zonas' ? <Zones {...props} /> : null}
            {section === 'compras' ? <Purchases {...props} /> : null}
            {section === 'armado' ? <Packing {...props} /> : null}
            {section === 'reclamos' ? <Claims {...props} /> : null}
            {section === 'incidencias' ? <Incidents {...props} /> : null}
            {section === 'devoluciones' ? <Refunds {...props} /> : null}
            {section === 'pines' ? <PinRequests {...props} /> : null}
            {section === 'conciliacion' ? <Balance {...props} /> : null}
            {section === 'metricas' ? <Metrics {...props} /> : null}
            {section === 'catalogo' ? <CatalogAdmin {...props} /> : null}
            {section === 'referencias' ? <References {...props} /> : null}
            {section === 'vecinos' ? <Neighbors {...props} /> : null}
            {section === 'cuentas' ? <Partners {...props} /> : null}
          </div>
        </main>
      </div>
    </div>
  );
}

interface SectionProps {
  cycle: string;
  setCycle: (cycle: string) => void;
  run: (action: () => Promise<unknown>, success: string) => Promise<boolean>;
  notify: AdminPanelProps['notify'];
  onViewAs?: AdminPanelProps['onViewAs'];
  role: Role;
}

const PROPOSAL_KIND: Record<string, { label: string; icon: IconName }> = {
  UNIR: { label: 'Unir zonas', icon: 'merge' },
  RECORDAR: { label: 'Recordar', icon: 'whatsapp' },
  INVITAR: { label: 'Invitar vecinos', icon: 'gift' },
  REVISAR_COSTO: { label: 'Revisar costo', icon: 'scale' },
  REACTIVAR: { label: 'Reactivar', icon: 'undo' },
};

function Zones({ cycle, setCycle, notify }: SectionProps) {
  const { data } = useLoad<Raw>(`/api/admin/analisis${cycle ? `?ciclo=${cycle}` : ''}`, notify);
  const mapZones = useMemo<MapZone[]>(() => (data?.zonas ?? []).map((z: Raw) => ({ id: z.id, name: z.nombre, group: z.grupo, lat: z.lat, lon: z.lon })), [data]);
  const mapUnions = useMemo<MapUnion[]>(() => (data?.uniones ?? []).map((u: Raw) => ({ a: u.a, b: u.b, distance: u.distancia_m, reason: u.motivo })), [data]);
  if (!data) return <AdminSkeleton />;
  const colors = groupColors(mapZones.map((z) => z.group));
  const nameOf = (id: string) => data.zonas.find((z: Raw) => z.id === id)?.nombre ?? id;
  const missing = data.zonas.length - drawableZones(mapZones).length;
  return (
    <>
      <section className="admin-intro"><div><h2>Zonas, uniones y propuestas</h2><p>Cada círculo es el radio de {data.radio_m} m de una zona; del mismo color, las zonas ya unidas. Las líneas muestran qué zonas están a {data.union_m} m o menos. Aquí solo se mira y se propone: la unión la piden y aceptan los admins de zona.</p></div><CycleSelect cycles={data.ciclos} value={data.ciclo} onChange={setCycle} /></section>

      <Card title="Mapa de zonas">
        <LazyZonesMap zones={mapZones} unions={mapUnions} radius={data.radio_m} mergeDistance={data.union_m} label="Mapa de las zonas de Yapa con su radio y las uniones posibles" />
        {missing ? <p className="admin-muted">{missing} {missing === 1 ? 'zona no tiene' : 'zonas no tienen'} ubicación y no se dibuja{missing === 1 ? '' : 'n'}.</p> : null}
        <ul className="zones-legend">{[...new Set(mapZones.map((z) => z.group))].map((g) => <li key={g}><span className="zones-dot" style={{ background: colors[g] }} />{mapZones.filter((z) => z.group === g).map((z) => z.name).join(' + ')}</li>)}</ul>
        {data.uniones.length ? <ul className="zones-unions">{data.uniones.map((u: Raw) => <li key={`${u.a}-${u.b}`} className={u.motivo ? 'is-blocked' : 'is-ok'}><span className="zones-union-icon" aria-hidden="true"><Icon name={u.motivo ? 'no' : 'merge'} size={16} /></span><strong>{nameOf(u.a)} ↔ {nameOf(u.b)}</strong><span>{unionLabel(u.distancia_m, u.motivo)}</span></li>)}</ul> : <p className="admin-muted">Ninguna zona está a {data.union_m} m o menos de otra de un grupo distinto.</p>}
      </Card>

      <Card title={`Propuestas del sistema (${data.propuestas.length})`}>
        {data.propuestas.length ? <div className="proposal-list">{data.propuestas.map((p: Raw) => { const kind = PROPOSAL_KIND[p.tipo] ?? { label: p.tipo, icon: 'info' as IconName }; return <article className="proposal" key={`${p.tipo}-${p.zonas.join('-')}`}><span className="proposal-icon"><Icon name={kind.icon} size={20} /></span><div><span className="proposal-kind">{kind.label}</span><h3>{humanizeWeeks(p.titulo)}</h3><p>{humanizeWeeks(p.detalle)}</p></div></article>; })}</div> : <Empty icon="ok" title="Nada que proponer" text="Cuando una zona pueda llegar al mínimo o pierda dinero, aparecerá aquí." />}
        <p className="admin-muted">Son sugerencias hechas con los pedidos de la semana: el sistema no ejecuta nada solo.</p>
      </Card>

      <Card title="Cómo va cada zona">
        <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Zona</th><th>Vecinos</th><th>Pedidos</th><th>Verificados</th><th>Adopción</th><th>Margen</th></tr></thead><tbody>{data.zonas.map((z: Raw) => <tr key={z.id}><td><span className="zones-dot" style={{ background: colors[z.grupo] }} /><strong>{z.nombre}</strong><small className="admin-cell-note">{z.distrito}{z.estado === 'ACTIVA' ? '' : ' · falta quien reciba'}</small></td><td>{z.vecinos}</td><td>{z.pedidos}</td><td>{z.verificados}</td><td>{z.adopcion} %</td><td className={z.margen !== null && num(z.margen) < 0 ? 'is-negative-text' : ''}>{marginLabel(z.margen)}</td></tr>)}</tbody></table></div>
        <p className="admin-muted">Adopción: pedidos de la semana entre vecinos de la zona. El margen aparece cuando la semana se liquida.</p>
      </Card>
    </>
  );
}

function Summary({ cycle, setCycle, run, notify }: SectionProps) {
  const { data, reload } = useLoad<Raw>(`/api/admin/resumen${cycle ? `?ciclo=${cycle}` : ''}`, notify);
  const [confirming, setConfirming] = useState(false);
  const [result, setResult] = useState<Raw | null>(null);
  useEffect(() => { setConfirming(false); setResult(null); }, [cycle]);
  if (!data) return <AdminSkeleton />;
  const pending: Order[] = data.por_verificar.map(toOrder);
  const orders: Order[] = data.pedidos.map(toOrder);
  const k = data.indicadores;
  const productName = (id: string) => orders.flatMap((o) => o.lines).find((l) => l.id === id)?.name ?? id;
  const verify = (order: Order) => run(() => api.post(`/api/admin/pedidos/${order.id}/verificar`), `Pago del pedido ${order.id} verificado.`).then(() => reload());
  const settle = async () => {
    try {
      setResult(await api.post<Raw>(`/api/admin/ciclos/${data.ciclo}/liquidar`));
      notify(`Semana del ${weekRangeLabel(data.ciclo)} liquidada.`, 'success');
      setConfirming(false);
      void reload();
    } catch (error) {
      notify(error instanceof Error ? error.message : 'No se pudo liquidar.', 'warning');
    }
  };
  return (
    <>
      <section className="admin-intro"><div><span className="admin-eyebrow">{weekRangeLabel(data.ciclo)}</span><h2>{data.abierto ? 'El ciclo recibe pedidos hasta el miércoles 20:00' : 'El ciclo ya no recibe pedidos'}</h2><p>Verifica los pagos con el código YP que cada vecino pone en su Yape o Plin. Después de la entrega, liquida para devolver el ahorro.</p></div><CycleSelect cycles={data.ciclos} value={data.ciclo} onChange={setCycle} /></section>
      <section className="admin-kpis" aria-label="Indicadores de la semana">
        <div className="admin-kpi"><span className="admin-kpi-label">Pedidos de la semana</span><strong>{k.pedidos}</strong><small>sin cancelados</small></div>
        <div className={`admin-kpi ${k.por_verificar ? 'admin-kpi--attention' : ''}`}><span className="admin-kpi-label">Pagos por verificar</span><strong>{k.por_verificar}</strong><small>{k.por_verificar ? 'busca el código YP en tu Yape' : 'todo verificado'}</small></div>
        <div className="admin-kpi"><span className="admin-kpi-label">Dinero verificado</span><strong>{formatMoney(num(k.verificado))}</strong><small>Yape y Plin</small></div>
        <div className="admin-kpi"><span className="admin-kpi-label">Vecinos con pedido</span><strong>{k.vecinos}</strong><small>esta semana</small></div>
      </section>

      <Card eyebrow="Mínimo de 8 por grupo" title="¿Qué grupos llegan?">
        <div className="admin-groups">{data.grupos.map((g: Raw) => <div className="admin-group" key={g.grupo}><div><strong>{g.zonas.join(' + ')}</strong></div><div className="admin-group-count"><span className={g.verificados >= g.minimo ? 'is-ready' : ''}>{g.verificados} / {g.minimo}</span><div className="progress-track"><span style={{ width: `${Math.min(g.verificados / g.minimo, 1) * 100}%` }} /></div></div></div>)}</div>
      </Card>

      <Card title={`Pagos por verificar (${pending.length})`}>
        {pending.length ? <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Pedido</th><th>Vecino</th><th>Yapea</th><th>Código en el mensaje</th><th><span className="sr-only">Acciones</span></th></tr></thead><tbody>{pending.map((o) => <tr key={o.id}><td><strong className="admin-order-code">{o.id}</strong></td><td>{o.customerName}</td><td><strong>{formatMoney(o.toPay)}</strong> <small>{o.method === 'PLIN' ? 'Plin' : 'Yape'}</small></td><td><code>{o.paymentCode}</code></td><td><ConfirmAction label={<><Icon name="check" size={15} /> Verificar</>} question={<>¿Ya viste <strong>{formatMoney(o.toPay)}</strong> con el código <code>{o.paymentCode}</code> en tu {o.method === 'PLIN' ? 'Plin' : 'Yape'}?</>} confirmLabel="Sí, verificar" onConfirm={() => verify(o)} /></td></tr>)}</tbody></table></div> : <Empty icon="ok" title="Todo verificado" text="Cuando un vecino pida, su código YP aparecerá aquí." />}
      </Card>

      <Card title={`Pedidos (${orders.length})`}>
        {orders.length ? <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Pedido</th><th>Vecino</th><th>Zona</th><th>Pagó</th><th>Estado</th></tr></thead><tbody>{orders.map((o) => <tr key={o.id}><td><strong className="admin-order-code">{o.id}</strong></td><td>{o.customerName}</td><td>{o.zoneName ?? o.zoneId}</td><td>{formatMoney(o.total)}{o.withBalance ? <small className="admin-cell-note">{formatMoney(o.withBalance)} con saldo</small> : null}</td><td><span className={`admin-order-status admin-order-status--${o.status === 'REGISTRADO' ? o.payment.toLowerCase() : o.status.toLowerCase()}`}>{o.status === 'REGISTRADO' && o.payment === 'POR_VERIFICAR' ? 'Por verificar' : statusLabel(o)}</span>{o.settlement ? <small className="admin-cell-note">costó {formatMoney(o.settlement.cost)} · devuelto {formatMoney(o.settlement.returned)}</small> : null}</td></tr>)}</tbody></table></div> : <Empty icon="truck" title="Esta semana todavía no tiene pedidos" text="Aparecerán apenas los vecinos confirmen." />}
        <div className="admin-settle">
          {result ? <div className="admin-settle-result"><strong>Semana liquidada</strong><p>Volvió a saldo {formatMoney(num(result.a_saldo))} · a reembolsar por Yape o Plin {formatMoney(num(result.reembolsado))}.</p><ul>{result.productos.map((p: Raw) => <li key={p.id}>{productName(p.id)}: {p.total} entre todos · tramo desde {p.tramo} · {formatMoney(num(p.precio_final))}</li>)}</ul></div>
            : data.liquidado ? <p>Esta semana ya está liquidada.</p>
              : confirming ? <div className="admin-settle-actions"><button className="primary-button" type="button" onClick={() => void settle()}>Sí, liquidar la semana</button><button className="secondary-button" type="button" onClick={() => setConfirming(false)}>Cancelar</button></div>
                : <><p>Liquidar calcula el precio final por tramo, el envío real por zona, los beneficios del admin de zona y devuelve el ahorro como saldo. Exige que todas las zonas estén entregadas o marcadas como fallidas.</p><button className="primary-button" type="button" disabled={!orders.length} onClick={() => setConfirming(true)}>Liquidar la semana <Icon name="arrow" size={17} /></button></>}
        </div>
      </Card>
    </>
  );
}

function Packing({ cycle, setCycle, run, notify, role }: SectionProps) {
  const packer = role === 'armador'; // S-290: el armador solo arma; la entrega la registra el reparto
  const { data, reload } = useLoad<Raw>(`/api/admin/armado${cycle ? `?ciclo=${cycle}` : ''}`, notify);
  const [failure, setFailure] = useState('PORTERIA_CERRADA');
  const [zoneFilter, setZoneFilter] = useState('');
  useEffect(() => { setZoneFilter(''); }, [cycle]);
  if (!data) return <AdminSkeleton />;
  const stops: Raw[] = data.paradas.filter((p: Raw) => !zoneFilter || p.zona.id === zoneFilter);
  const orders: Order[] = data.pedidos.map(toOrder).filter((o: Order) => !zoneFilter || o.zoneId === zoneFilter);
  const packed = orders.filter((o) => o.bags?.length).length;
  const send = (path: string, form: FormData, extra: Record<string, string>, success: string) => {
    for (const [key, value] of Object.entries(extra)) form.set(key, value);
    return run(() => api.post(path, form), success).then(async (ok) => { await reload(); return ok; });
  };
  return (
    <>
      <section className="admin-intro"><div><h2>{packer ? 'Arma cada bolsa y tómale foto' : 'Foto de cada bolsa y de cada entrega'}</h2><p>{packer ? 'Solo aparecen los pedidos de grupos que llegaron al mínimo. Marca cada producto al meterlo y toma la foto de la bolsa: sin bolsas, el reparto no puede salir.' : 'Solo aparecen los pedidos de grupos que llegaron al mínimo. Sin foto no se puede entregar.'}</p></div><CycleSelect cycles={data.ciclos} value={data.ciclo} onChange={setCycle} /></section>
      {data.paradas.length > 1 ? <label className="checkout-field packing-zone-filter"><span>Edificio</span><select value={zoneFilter} onChange={event => setZoneFilter(event.target.value)}><option value="">Todas las zonas</option>{data.paradas.map((p: Raw) => <option key={p.zona.id} value={p.zona.id}>{p.zona.nombre}</option>)}</select></label> : null}
      {orders.length ? <div className="pack-progress" role="status"><div><strong>{packed} de {orders.length} pedidos con bolsa</strong><span>{packed === orders.length ? 'Todo armado: el reparto ya puede salir.' : `Faltan ${orders.length - packed}.`}</span></div><div className="progress-track"><span style={{ width: `${(packed / orders.length) * 100}%` }} /></div></div> : null}
      {orders.length ? <div className="pack-list">{orders.map((o) => <PackCard key={o.id} order={o} send={send} />)}</div> : <Card title="Nada que armar"><Empty icon="box" title="Nada que armar" text="Los pedidos aparecen cuando su grupo llega al mínimo." /></Card>}
      <Card title={`Entregas por zona (${stops.length})`}>
        {stops.length ? <div className="stop-list">{stops.map((p: Raw) => { const zone: Zone = toZone(p.zona); return (
          <div className="stop-card" key={zone.id}>
            <div className="stop-head"><strong>{zone.name}</strong><span>{zone.district}</span>{p.entrega ? <span className="state-pill state-pill--ok"><Icon name="check" size={13} /> Entregada a {p.entrega.recibe}</span> : p.fallida ? <span className="state-pill state-pill--bad">Entrega fallida</span> : p.en_camino ? <span className="state-pill"><Icon name="truck" size={13} /> En camino</span> : <span className="state-pill">Por entregar</span>}</div>
            {!packer && !p.entrega && !p.fallida ? <div className="stop-actions">
              {p.en_camino ? null : <button className="admin-row-button" type="button" onClick={() => void send('/api/admin/salidas', new FormData(), { ciclo: data.ciclo, zona: zone.id }, `El reparto salió hacia ${zone.name}: los vecinos reciben el aviso.`)}>Salió el reparto</button>}
              <PhotoForm label="Registrar entrega" onSend={(form) => send('/api/admin/entregas', form, { ciclo: data.ciclo, zona: zone.id }, `Entrega en ${zone.name} registrada.`)}><label className="checkout-field"><span>¿Quién recibió?</span><input name="recibe" defaultValue={zone.contact} required /></label></PhotoForm>
              <details><summary>No pudimos entregar</summary><div className="segmented">{FAILURES.map((f) => <button key={f.value} type="button" className={failure === f.value ? 'is-active' : ''} onClick={() => setFailure(f.value)}>{f.label}</button>)}</div><PhotoForm label="Registrar entrega fallida" onSend={(form) => send('/api/admin/entregas-fallidas', form, { ciclo: data.ciclo, zona: zone.id, motivo: failure }, 'Entrega fallida registrada: se devuelve todo menos el envío.')} /></details>
            </div> : null}
          </div>); })}</div> : <Empty icon="truck" title="No hay zonas que se atiendan" text="Ningún grupo llegó al mínimo en esta semana." />}
      </Card>
    </>
  );
}

// S-331: una tarjeta por pedido; las marcas son una ayuda en pantalla y la bolsa se registra al elegir la foto
function PackCard({ order, send }: { order: Order; send: (path: string, form: FormData, extra: Record<string, string>, success: string) => Promise<boolean> }) {
  const [checked, setChecked] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [damaged, setDamaged] = useState(false);
  const bags = order.bags?.length ?? 0;
  const upload = async (input: HTMLInputElement) => {
    const file = input.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.set('foto_archivo', file);
    setBusy(true);
    await send('/api/admin/bolsas', form, { pedido: String(order.id) }, `Bolsa ${bags + 1} del pedido ${order.id} registrada.`);
    setBusy(false);
    input.value = '';
  };
  const all = order.lines.length > 0 && checked.length === order.lines.length;
  return (
    <article className={`pack-card${bags ? ' is-packed' : ''}`}>
      <header className="pack-card-head">
        <div><strong>Pedido {order.id}</strong><span>{order.customerName}{order.zoneName ? ` · ${order.zoneName}` : ''}</span></div>
        <span className={`state-pill${bags ? ' state-pill--ok' : ''}`}>{bags ? `${bags} ${bags === 1 ? 'bolsa' : 'bolsas'}` : 'Sin bolsa'}</span>
      </header>
      <ul className="pack-lines" aria-label={`Productos del pedido ${order.id}`}>{order.lines.map((l) => {
        const done = checked.includes(l.id);
        return <li key={l.id}><label className={done ? 'is-checked' : ''}><input type="checkbox" checked={done} onChange={() => setChecked((c) => (done ? c.filter((x) => x !== l.id) : [...c, l.id]))} /><ProductThumb id={l.id} size={40} /><span className="pack-line-name">{l.name}</span><strong>{amountWithUnit(l.quantity, l.unit, formatQuantity)}</strong></label></li>;
      })}</ul>
      {bags ? <ul className="pack-bags" aria-label={`Bolsas registradas del pedido ${order.id}`}>{order.bags!.map((b) => <li key={b.number}><a href={photoUrl(b.photo)} target="_blank" rel="noopener"><img src={photoUrl(b.photo)} alt={`Foto de la bolsa ${b.number} del pedido ${order.id}`} width="56" height="56" loading="lazy" /><small>Bolsa {b.number}</small></a></li>)}</ul> : null}
      <p className="pack-labels"><Icon name="tag" size={15} />{order.labels?.length ? order.labels.join(' · ') : `Rotula la bolsa: Pedido ${order.id}${order.zoneName ? ` · ${order.zoneName}` : ''}`}</p>
      <label className={`pack-camera${all || bags ? ' is-ready' : ''}${busy ? ' is-busy' : ''}`}>
        <Icon name="camera" size={22} />
        <span>{busy ? 'Subiendo la foto…' : bags ? 'Tomar foto de otra bolsa' : 'Tomar foto de la bolsa'}</span>
        <input type="file" accept="image/*" capture="environment" disabled={busy} onChange={(event) => void upload(event.currentTarget)} aria-label={`Foto de la bolsa del pedido ${order.id}`} />
      </label>
      <button className="text-button pack-damaged-toggle" type="button" aria-expanded={damaged} onClick={() => setDamaged((d) => !d)}>Algo llegó dañado</button>
      {damaged ? <PhotoForm label="Registrar dañado" onSend={(form) => send('/api/admin/danados', form, { pedido: String(order.id) }, `Dañado del pedido ${order.id} registrado: se repone con el colchón o se devuelve en la liquidación.`)}><label className="checkout-field"><span>Producto</span><select name="producto" required>{order.lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}</select></label><label className="checkout-field"><span>Cantidad</span><input name="cantidad" inputMode="decimal" placeholder="1" required /></label></PhotoForm> : null}
    </article>
  );
}

function ClaimPhoto({ route, who }: { route: string; who: string }) {
  const [failed, setFailed] = useState(false);
  if (!route) return <small>Sin foto</small>;
  if (failed) return <small>No se pudo cargar la foto</small>;
  return <a className="claim-photo" href={photoUrl(route)} target="_blank" rel="noopener" aria-label={`Abrir la foto del reclamo de ${who}`}><img src={photoUrl(route)} alt={`Foto del reclamo de ${who}`} width="64" height="64" loading="lazy" onError={() => setFailed(true)} /></a>;
}

const PRIORITY: Record<string, string> = { ALTA: 'Prioridad alta', MEDIA: 'Prioridad media', BAJA: 'Prioridad baja' };

// iteración 61: la IA sugiere categoría, prioridad y un borrador; quien atiende decide (no cambia nada)
function AiDraft({ kind, id }: { kind: 'reclamo' | 'incidencia'; id: number }) {
  const [busy, setBusy] = useState(false);
  const [draft, setDraft] = useState<Raw | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const ask = async () => {
    setBusy(true);
    setError('');
    try {
      setDraft(await api.post<Raw>('/api/admin/ia/atencion', { tipo: kind, id }));
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'La IA no respondió.');
    } finally {
      setBusy(false);
    }
  };
  const copy = async () => {
    try { await navigator.clipboard.writeText(draft?.borrador ?? ''); setCopied(true); } catch { setCopied(false); }
  };
  if (!draft) return <><button className="text-button" type="button" disabled={busy} onClick={() => void ask()}>{busy ? 'Pensando…' : 'Sugerir con IA'}</button>{error ? <small className="admin-cell-note">{error}</small> : null}</>;
  return (
    <div className="ai-draft" aria-live="polite">
      <div className="ai-draft-meta"><span className="state-pill">{AI_CATEGORIES[draft.categoria] ?? draft.categoria}</span><span className="state-pill">{PRIORITY[draft.prioridad] ?? draft.prioridad}</span></div>
      <p>{draft.borrador}</p>
      <div className="ai-draft-meta"><button className="admin-row-button" type="button" onClick={() => void copy()}>{copied ? '¡Copiado!' : 'Copiar respuesta'}</button><button className="text-button" type="button" onClick={() => setDraft(null)}>Cerrar</button></div>
    </div>
  );
}

function Claims({ run, notify }: SectionProps) {
  const { data, reload } = useLoad<Raw>('/api/admin/reclamos', notify);
  if (!data) return <AdminSkeleton />;
  const review = (id: number, decision: 'aprobar' | 'rechazar') => run(() => api.post(`/api/admin/reclamos/${id}/revisar`, { decision }), `Reclamo ${id} ${decision === 'aprobar' ? 'aprobado: se devuelve como saldo' : 'rechazado'}.`).then(() => reload());
  const pending = data.reclamos.filter((c: Raw) => c.estado === 'PENDIENTE');
  const done = data.reclamos.filter((c: Raw) => c.estado !== 'PENDIENTE');
  const item = (c: Raw) => <div className="claim-item"><ProductThumb id={c.producto} size={44} /><div><strong>{c.nombre ?? c.producto} × {c.cantidad}</strong><span>{c.vecino} · pedido {c.pedido}</span></div></div>;
  return (
    <>
      <Card eyebrow="Por artículo, con foto" title={`Pendientes (${pending.length})`}>
        {pending.length ? <div className="work-list">{pending.map((c: Raw) => (
          <article className="work-card" key={c.id}>
            <div className="work-card-top">{item(c)}<span className="state-pill">{REASONS[c.motivo] ?? c.motivo}</span></div>
            <ClaimPhoto route={c.foto} who={c.vecino} />
            <div className="work-actions"><ConfirmAction label="Aprobar" confirmLabel="Sí, aprobar" question={<>Reclamo de {c.vecino}: {claimEffect('aprobar')}. ¿Aprobar?</>} onConfirm={() => review(c.id, 'aprobar')} /><ConfirmAction label="Rechazar" className="secondary-button" confirmLabel="Sí, rechazar" question={<>Reclamo de {c.vecino}: {claimEffect('rechazar')}. ¿Rechazar?</>} onConfirm={() => review(c.id, 'rechazar')} /></div>
            <AiDraft kind="reclamo" id={c.id} />
          </article>
        ))}</div> : <Empty icon="ok" title="Sin reclamos pendientes" text="Los vecinos reclaman hasta 24 h después de la entrega." />}
      </Card>
      <Card title={`Completados (${done.length})`}>{done.length ? <div className="work-list">{done.map((c: Raw) => (
        <article className="work-card work-card--done" key={c.id}>
          <div className="work-card-top">{item(c)}<span className={`state-pill ${c.estado === 'APROBADO' ? 'state-pill--ok' : 'state-pill--bad'}`}>{CLAIM_STATUS[c.estado] ?? c.estado}</span></div>
          <p className="admin-muted">{c.estado === 'APROBADO' ? `Volvió ${formatMoney(num(c.devuelto))} a su saldo.` : 'No se devolvió dinero.'}</p>
        </article>
      ))}</div> : <Empty icon="ok" title="Todavía no hay reclamos completados" text="Aquí aparecerán los reclamos aprobados y rechazados, con su resultado." />}</Card>
    </>
  );
}

const shortDay = (iso: string | null) => (iso ? new Date(`${iso}T12:00:00`).toLocaleDateString('es-PE', { weekday: 'short', day: 'numeric', month: 'short' }) : 'sin fecha');

function Refunds({ run, notify }: SectionProps) {
  const { data, reload } = useLoad<Raw>('/api/admin/devoluciones', notify);
  const [codes, setCodes] = useState<Record<number, string>>({});
  if (!data) return <AdminSkeleton />;
  const pay = (id: number) => run(() => api.post(`/api/admin/devoluciones/${id}/pagar`, { codigo: codes[id] ?? '' }), `Devolución ${id} marcada como pagada.`).then(() => reload());
  return (
    <Card eyebrow="Plazo: hasta 30 días" title={`Por devolver a Yape o Plin (${data.devoluciones.length})`}>
      {data.devoluciones.length ? <div className="work-list">{data.devoluciones.map((r: Raw) => (
        <article className="work-card" key={r.id}>
          <div className="work-card-top"><div className="claim-item"><span className="work-icon" aria-hidden="true"><Icon name="undo" size={20} /></span><div><strong>{r.vecino}</strong><span>{REASONS[r.motivo] ?? 'Devolución'} · vence el {shortDay(r.vence)}</span></div></div><strong className="work-amount">{formatMoney(num(r.monto))}</strong></div>
          <label className="checkout-field"><span>N.º de operación de tu Yape o Plin</span><input value={codes[r.id] ?? ''} onChange={(event) => setCodes((c) => ({ ...c, [r.id]: event.target.value }))} placeholder="Ej. 04512873" inputMode="numeric" autoComplete="off" /></label>
          <button className="primary-button" type="button" disabled={!codes[r.id]?.trim()} onClick={() => void pay(r.id)}>Ya le devolví {formatMoney(num(r.monto))}</button>
        </article>
      ))}</div> : <Empty icon="ok" title="No hay devoluciones pendientes" text="Zonas sin mínimo, cancelaciones y saldos pedidos de vuelta aparecen aquí." />}
    </Card>
  );
}

function Balance({ notify }: SectionProps) {
  const { data } = useLoad<Raw>('/api/admin/conciliacion', notify);
  if (!data) return <AdminSkeleton />;
  const rows: Array<[string, string]> = [['Recibido por Yape y Plin', data.recibido], ['En curso (pedidos sin liquidar)', data.en_curso], ['Retenido por Yapa', data.retenido], ['Deuda con vecinos (saldos y devoluciones)', data.deuda], ['Devoluciones ya pagadas', data.devoluciones_pagadas]];
  return (
    <>
      <section className={`balance-banner ${data.cuadra ? 'is-ok' : 'is-bad'}`}><Icon name={data.cuadra ? 'ok' : 'warning'} size={34} weight="duotone" /><div><strong>{data.cuadra ? 'El dinero cuadra al céntimo' : 'No cuadra: revisar antes de seguir'}</strong><span>recibido = en curso + retenido + deuda + devoluciones pagadas · diferencia {formatMoney(num(data.diferencia))}</span></div></section>
      <Card title="De dónde viene y a dónde va"><div className="admin-table-wrap"><table className="admin-table balance-table"><tbody>{rows.map(([label, value]) => <tr key={label}><td>{label}</td><td><strong>{formatMoney(num(value))}</strong></td></tr>)}<tr className="is-total"><td>Diferencia</td><td><strong>{formatMoney(num(data.diferencia))}</strong></td></tr></tbody></table></div></Card>
    </>
  );
}

function Metrics({ notify }: SectionProps) {
  const [cycle, setCycle] = useState(''); // propio de Métricas: por defecto, la última semana cerrada
  const [data, setData] = useState<Raw | null>(null);
  const [error, setError] = useState('');
  const [cycles, setCycles] = useState<string[]>([]);
  useEffect(() => {
    let active = true;
    api.get<Raw>('/api/admin/resumen').then((s) => { if (active) { setCycles(s.ciclos); setCycle((c) => c || (s.ciclos.find((x: string) => x !== s.ciclo) ?? s.ciclo)); } }).catch(() => undefined);
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (!cycle) return;
    api.get<Raw>(`/api/admin/metricas?ciclo=${cycle}`).then((d) => { setData(d); setError(''); }).catch((e) => { setData(null); setError(e instanceof Error ? e.message : 'Sin datos'); });
  }, [cycle, notify]);
  const margins = data?.margenes ?? [];
  const avg = margins.length ? margins.reduce((s: number, m: Raw) => s + num(m.margen), 0) / margins.length : 0;
  return (
    <>
      <section className="admin-intro"><div><h2>¿El modelo se sostiene?</h2><p>Margen por pedido antes de costos operativos, ahorro entregado y recompra de la semana 4.</p></div><CycleSelect cycles={cycles} value={cycle} onChange={setCycle} /></section>
      {error ? <Empty icon="info" title="Esta semana aún no tiene métricas" text={error} /> : data ? <>
        <section className="admin-kpis">
          <div className="admin-kpi"><span className="admin-kpi-label">Margen promedio</span><strong>{formatMoney(avg)}</strong><small>por pedido</small></div>
          <div className="admin-kpi"><span className="admin-kpi-label">Ahorro entregado</span><strong>{formatMoney(num(data.ahorro.total))}</strong><small>volumen {formatMoney(num(data.ahorro.volumen))} · envío {formatMoney(num(data.ahorro.envio))}</small></div>
          <div className="admin-kpi"><span className="admin-kpi-label">Frente al supermercado</span><strong>{data.frente_a.SUPERMERCADO?.porcentaje ? `${data.frente_a.SUPERMERCADO.porcentaje} %` : '—'}</strong><small>{data.frente_a.SUPERMERCADO?.canastas ?? 0} canastas comparadas</small></div>
          <div className={`admin-kpi ${data.recompra.error ? '' : data.recompra.cumple ? '' : 'admin-kpi--attention'}`}><span className="admin-kpi-label">Recompra semana 4</span><strong>{data.recompra.error ? '—' : `${data.recompra.tasa} %`}</strong><small>{data.recompra.error ? humanizeWeeks(String(data.recompra.error.mensaje)) : `meta 50 % · ${data.recompra.volvieron} de ${data.recompra.vecinos}`}</small></div>
        </section>
        {data.margen_real ? <section className="admin-kpis">
          <div className={`admin-kpi ${data.margen_real.pierden ? 'admin-kpi--attention' : ''}`}><span className="admin-kpi-label">Margen real</span><strong>{data.margen_real.promedio != null ? formatMoney(num(data.margen_real.promedio)) : '—'}</strong><small>por pedido, con flete, armado y atención; cobro por Plin sin comisión</small></div>
          <div className="admin-kpi"><span className="admin-kpi-label">Flete de la compra</span><strong>{formatMoney(num(data.margen_real.flete))}</strong><small>{data.margen_real.estimado ? 'estimado: compras aún no lo registra' : 'registrado por compras'} · {formatMoney(num(data.margen_real.por_pedido))} por pedido</small></div>
          <div className="admin-kpi"><span className="admin-kpi-label">Pedidos que pierden</span><strong>{data.margen_real.pierden}</strong><small>con los costos reales</small></div>
        </section> : null}
        <Card title="Margen antes de costos operativos"><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Pedido</th><th>Cobrado</th><th>Reclamos</th><th>Proveedor</th><th>Parada</th><th>Margen</th></tr></thead><tbody>{margins.map((m: Raw) => <tr key={m.pedido} className={m.negativo ? 'is-negative' : ''}><td>{m.pedido}</td><td>{formatMoney(num(m.cobrado))}</td><td>{formatMoney(num(m.reclamos))}</td><td>{formatMoney(num(m.proveedor))}</td><td>{formatMoney(num(m.parada))}</td><td><strong>{formatMoney(num(m.margen))}</strong></td></tr>)}</tbody></table></div></Card>
      </> : <AdminSkeleton />}
    </>
  );
}

function CatalogAdmin({ run, notify }: SectionProps) {
  const [week, setWeek] = useState(''); // por defecto, la semana siguiente (S-117)
  const { data, reload } = useLoad<Raw>(`/api/admin/catalogo${week ? `?ciclo=${week}` : ''}`, notify);
  const [text, setText] = useState('');
  useEffect(() => { if (data) setText(data.lista); }, [data]);
  if (!data) return <AdminSkeleton />;
  const deactivate = (id: string) => run(() => api.post('/api/admin/catalogo/desactivar', { ciclo: data.ciclo, producto: id }), 'Producto desactivado para esa semana.').then(() => reload());
  const publish = () => run(() => api.post('/api/admin/catalogo', { ciclo: data.ciclo, lista: text }), `Catálogo del ${weekRangeLabel(data.ciclo)} publicado.`).then(() => reload());
  return (
    <>
      <section className="admin-intro"><div><h2>{weekRangeLabel(data.ciclo)} · {data.publicado ? 'publicado' : 'usa el catálogo base'}</h2><p>Precio máximo = primer tramo del proveedor más la comisión. Se publica antes del lunes 00:00.</p></div><CycleSelect cycles={data.ciclos} value={data.ciclo} onChange={setWeek} /></section>
      <Card title={`Productos (${data.productos.length})`}>
        <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Producto</th><th>Precio máximo</th><th>Tramos del proveedor</th><th>Máximo</th><th>Estado</th></tr></thead><tbody>{data.productos.map((p: Raw) => <tr key={p.id} className={p.activo ? '' : 'is-muted'}><td><strong>{p.nombre}</strong><small className="admin-cell-note">por {p.unidad}</small></td><td>{formatMoney(num(p.precio_max))}</td><td><small className="admin-tiers">{p.tramos.map((t: Raw) => `desde ${t.desde}: ${formatMoney(num(t.precio))}`).join(' · ')}</small></td><td>{p.maximo} {p.unidad}</td><td>{p.activo ? <button className="text-button" type="button" onClick={() => void deactivate(p.id)}>Desactivar</button> : <span className="state-pill">Desactivado</span>}</td></tr>)}</tbody></table></div>
      </Card>
      <details className="admin-card plegable"><summary>Publicar la lista del proveedor</summary><p className="admin-muted">Una línea por producto, separada por comas. Se publica todo o nada.</p><textarea className="admin-textarea" rows={10} value={text} onChange={(event) => setText(event.target.value)} /><button className="primary-button" type="button" onClick={() => void publish()}>Publicar esta semana</button></details>
    </>
  );
}

function References({ run, notify }: SectionProps) {
  const { data, reload } = useLoad<Raw>('/api/admin/referencias', notify);
  const [product, setProduct] = useState('');
  const [kind, setKind] = useState<'MERCADO' | 'SUPERMERCADO'>('MERCADO');
  const [price, setPrice] = useState('');
  const [source, setSource] = useState('');
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10));
  if (!data) return <AdminSkeleton />;
  const save = (event: FormEvent) => { event.preventDefault(); void run(() => api.post('/api/admin/referencias', { producto: product || data.productos[0]?.id, tipo: kind, precio: price, fuente: source, fecha: date }), 'Precio de referencia guardado.').then((ok) => { if (ok) { setPrice(''); void reload(); } }); };
  const cell = (ref: Raw | undefined) => ref ? <><strong>{formatMoney(num(ref.precio))}</strong><small className="admin-cell-note">{ref.fuente} · {shortDate(ref.visto) || ref.visto} · {Math.round(num(ref.ahorro))} % de ahorro</small></> : <span className="admin-muted">—</span>;
  return (
    <>
      <Card eyebrow="Vigencia: 14 días" title="¿Cuánto costaría en otro lado?"><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Producto</th><th>Máximo Yapa</th><th>Mercado de barrio</th><th>Supermercado</th></tr></thead><tbody>{data.productos.map((p: Raw) => <tr key={p.id}><td><span className="cell-with-thumb"><ProductThumb id={p.id} size={32} /><strong>{p.nombre}</strong></span></td><td>{formatMoney(num(p.precio_max))}</td><td>{cell(p.referencias.MERCADO)}</td><td>{cell(p.referencias.SUPERMERCADO)}</td></tr>)}</tbody></table></div></Card>
      <form className="admin-card" onSubmit={save}><div className="admin-card-heading"><div><h2>Registrar un precio visto</h2></div></div>
        <div className="form-grid"><label className="checkout-field"><span>Producto</span><select value={product} onChange={(event) => setProduct(event.target.value)}>{data.productos.map((p: Raw) => <option key={p.id} value={p.id}>{p.nombre}</option>)}</select></label>
          <div className="checkout-field"><span>Dónde</span><div className="segmented">{(['MERCADO', 'SUPERMERCADO'] as const).map((k) => <button type="button" key={k} className={kind === k ? 'is-active' : ''} onClick={() => setKind(k)}>{k === 'MERCADO' ? 'Mercado de barrio' : 'Supermercado'}</button>)}</div></div>
          <label className="checkout-field"><span>Precio (S/)</span><input value={price} onChange={(event) => setPrice(event.target.value)} inputMode="decimal" placeholder="0.00" required /></label>
          <label className="checkout-field"><span>Fuente</span><input value={source} onChange={(event) => setSource(event.target.value)} placeholder="Ej. Mercado de Lince" required /></label>
          <label className="checkout-field"><span>Fecha</span><input type="date" value={date} onChange={(event) => setDate(event.target.value)} required /></label></div>
        <button className="primary-button" type="submit">Guardar precio</button></form>
    </>
  );
}

function Neighbors({ run, notify, onViewAs }: SectionProps) {
  const { data, reload } = useLoad<Raw>('/api/admin/vecinos', notify);
  const { data: zoneData } = useLoad<Raw>('/api/zonas', notify);
  const { data: pinData, reload: reloadPins } = useLoad<Raw>('/api/admin/pin-solicitudes', notify);
  const [form, setForm] = useState({ nombre: '', celular: '', correo: '', zona: '', referido: '', consentimiento: false });
  const [created, setCreated] = useState<Raw | null>(null);
  const [query, setQuery] = useState('');
  if (!data) return <AdminSkeleton />;
  const shown: Raw[] = filterNeighbors(data.vecinos, query);
  const zones: Zone[] = (zoneData?.zonas ?? []).map(toZone);
  const register = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const result = await api.post<Raw>('/api/admin/vecinos', { ...form, zona: form.zona || zones[0]?.id, celular: form.celular.replace(/\s/g, '') });
      setCreated({ ...result, celular: form.celular.replace(/\s/g, '') });
      setForm({ nombre: '', celular: '', correo: '', zona: form.zona, referido: '', consentimiento: false });
      notify(`Vecino ${result.id} registrado.`, 'success');
      void reload();
    } catch (error) {
      notify(error instanceof Error ? error.message : 'No se pudo registrar.', 'warning');
    }
  };
  const resetPin = (id: number, celular: string | null) => run(async () => { const r = await api.post<Raw>(`/api/admin/vecinos/${id}/pin`); setCreated({ ...r, nombre: data.vecinos.find((v: Raw) => v.id === id)?.nombre, celular }); }, 'PIN nuevo generado.');
  const dismissPin = (id: number) => run(() => api.post(`/api/admin/pin-solicitudes/${id}/descartar`), 'Solicitud descartada.').then(() => reloadPins());
  return (
    <>
      {created ? <PinBanner created={created} onClose={() => setCreated(null)} /> : null}
      {pinData?.solicitudes.length ? <Card title={`Solicitudes de PIN (${pinData.solicitudes.length})`}><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Vecino</th><th>Celular registrado</th><th>Pidió</th><th><span className="sr-only">Acciones</span></th></tr></thead><tbody>{pinData.solicitudes.map((r: Raw) => <tr key={r.id}><td><strong>{r.vecino}</strong><small className="admin-cell-note">Cliente {r.cliente}</small></td><td>{r.celular ?? 'Sin celular'}</td><td>{new Date(r.hora).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' })}</td><td className="row-actions"><button className="admin-row-button" type="button" onClick={() => void resetPin(r.cliente, r.celular).then(() => reloadPins())}>Nuevo PIN y escribir</button><ConfirmAction label="Descartar" className="text-button" confirmLabel="Sí, descartar" question={<>¿Descartar? El PIN de {r.vecino} no cambia.</>} onConfirm={() => dismissPin(r.id)} /></td></tr>)}</tbody></table></div><p className="admin-muted">El PIN nuevo se manda al celular que el vecino registró: así solo lo recibe quien tiene ese teléfono.</p></Card> : null}
      <form className="admin-card" onSubmit={register}><div className="admin-card-heading"><div><h2>Dar de alta a un vecino</h2></div></div>
        <div className="form-grid"><label className="checkout-field"><span>Nombre</span><input value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} required /></label>
          <label className="checkout-field"><span>Celular</span><input value={form.celular} onChange={(event) => setForm({ ...form, celular: event.target.value.replace(/[^\d\s]/g, '') })} inputMode="numeric" placeholder="9XX XXX XXX" required /></label>
          <label className="checkout-field"><span>Correo</span><input type="email" value={form.correo} onChange={(event) => setForm({ ...form, correo: event.target.value })} placeholder="nombre@gmail.com" autoComplete="off" required /></label>
          <label className="checkout-field"><span>Zona</span><select value={form.zona} onChange={(event) => setForm({ ...form, zona: event.target.value })}>{zones.map((z) => <option key={z.id} value={z.id}>{z.name} · {z.district}</option>)}</select></label>
          <label className="checkout-field"><span>Código de quien lo invitó <small>opcional</small></span><input value={form.referido} onChange={(event) => setForm({ ...form, referido: event.target.value.toUpperCase() })} placeholder="Ej. ANA101" /></label></div>
        <label className="choice-row"><input type="checkbox" checked={form.consentimiento} onChange={(event) => setForm({ ...form, consentimiento: event.target.checked })} /><span className="choice-mark choice-mark--check" /><span className="choice-copy"><strong>El vecino aceptó que Yapa guarde su nombre, celular y correo para sus pedidos</strong><small>Sin consentimiento no se guarda nada.</small></span></label>
        <button className="primary-button" type="submit" disabled={!form.consentimiento}>Registrar y generar PIN</button></form>
      <Card title={`Vecinos (${query.trim() ? `${shown.length} de ${data.vecinos.length}` : data.vecinos.length})`} aside={<label className="admin-search"><span className="sr-only">Buscar vecino</span><input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Nombre, número o celular" /></label>}><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>N.º</th><th>Nombre</th><th>Celular</th><th>Zona</th><th>Consentimiento</th><th><span className="sr-only">Acciones</span></th></tr></thead><tbody>{shown.map((v: Raw) => <tr key={v.id}><td>{v.id}</td><td><strong>{v.nombre}</strong>{v.suspendido ? <small className="admin-cell-warning">suspendido</small> : null}</td><td>{v.celular ?? '—'}</td><td>{zones.find((z) => z.id === v.zona)?.name ?? v.zona}</td><td><small>{v.consentimiento ? shortDate(v.consentimiento.slice(0, 10)) : '—'}</small></td><td><button className="text-button" type="button" onClick={() => void resetPin(v.id, v.celular)}>Nuevo PIN</button>{onViewAs ? <button className="text-button" type="button" onClick={() => void onViewAs(v.id)}>Ver como</button> : null}</td></tr>)}</tbody></table></div>{shown.length ? null : <p className="admin-muted">Ningún vecino coincide con la búsqueda.</p>}</Card>
    </>
  );
}

const OFFER_STATES: Record<string, string> = { PENDIENTE: 'Por revisar', APROBADA: 'Aprobada', RECHAZADA: 'Rechazada' };

// iteración 54: cuentas de proveedores y transportistas, y las listas que mandan los proveedores
function PinBanner({ created, onClose }: { created: Raw; onClose: () => void }) {
  const welcome = `Hola ${String(created.nombre ?? '').split(' ')[0]}, ya estás en Yapa. Entra con tu número de cliente ${created.id} y tu PIN ${created.pin}. Te recomendamos cambiarlo al entrar.`;
  return <section className="pin-banner"><Icon name="ok" size={30} weight="duotone" /><div><strong>Cliente {created.id} · PIN {created.pin}</strong><span>Se muestra una sola vez. Envíaselo por WhatsApp.</span></div><a className="primary-button" href={`https://wa.me/${created.celular ? `51${created.celular}` : ''}?text=${encodeURIComponent(welcome)}`} target="_blank" rel="noreferrer"><Icon name="whatsapp" size={17} /> Enviar</a><button className="icon-button" type="button" onClick={onClose} aria-label="Cerrar"><Icon name="close" size={18} /></button></section>;
}

// iteración 55, AT-03: atención responde los "Olvidé mi PIN" sin ver la lista completa de vecinos
function PinRequests({ run, notify }: SectionProps) {
  const { data, reload } = useLoad<Raw>('/api/admin/pin-solicitudes', notify);
  const [created, setCreated] = useState<Raw | null>(null);
  if (!data) return <AdminSkeleton />;
  const resetPin = (r: Raw) => run(async () => { const result = await api.post<Raw>(`/api/admin/vecinos/${r.cliente}/pin`); setCreated({ ...result, nombre: r.vecino, celular: r.celular }); }, 'PIN nuevo generado.').then(() => reload());
  const dismiss = (id: number) => run(() => api.post(`/api/admin/pin-solicitudes/${id}/descartar`), 'Solicitud descartada.').then(() => reload());
  return (
    <>
      {created ? <PinBanner created={created} onClose={() => setCreated(null)} /> : null}
      <Card eyebrow="Olvidé mi PIN" title={`Por atender (${data.solicitudes.length})`}>
        {data.solicitudes.length ? <><div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Vecino</th><th>Celular registrado</th><th>Pidió</th><th><span className="sr-only">Acciones</span></th></tr></thead><tbody>{data.solicitudes.map((r: Raw) => <tr key={r.id}><td><strong>{r.vecino}</strong><small className="admin-cell-note">Cliente {r.cliente}</small></td><td>{r.celular ?? 'Sin celular'}</td><td>{new Date(r.hora).toLocaleString('es-PE', { dateStyle: 'short', timeStyle: 'short' })}</td><td className="row-actions"><button className="admin-row-button" type="button" onClick={() => void resetPin(r)}>Nuevo PIN y escribir</button><ConfirmAction label="Descartar" className="text-button" confirmLabel="Sí, descartar" question={<>¿Descartar? El PIN de {r.vecino} no cambia.</>} onConfirm={() => dismiss(r.id)} /></td></tr>)}</tbody></table></div><p className="admin-muted">El PIN nuevo se manda al celular que el vecino registró: así solo lo recibe quien tiene ese teléfono.</p></> : <Empty icon="ok" title="Nadie pidió ayuda con su PIN" text="Cuando un vecino use «Olvidé mi PIN» y no tenga correo verificado, aparece aquí." />}
      </Card>
    </>
  );
}

// iteración 55, CP-01..CP-03: el encargado de compras ve qué comprar a cada proveedor y maneja el colchón
function Incidents({ run, notify }: SectionProps) {
  const { data, reload } = useLoad<Raw>('/api/admin/incidencias', notify);
  const [week, setWeek] = useState('');
  const { data: orderData } = useLoad<Raw>(`/api/admin/pedidos${week ? `?ciclo=${week}` : ''}`, notify);
  const [draft, setDraft] = useState({ pedido: '', tipo: 'ENTREGA', descripcion: '' });
  const [search, setSearch] = useState('');
  const [notes, setNotes] = useState<Record<number, string>>({});
  if (!data) return <AdminSkeleton />;
  // S-329: el pedido se elige de la lista; la búsqueda filtra por número, vecino o edificio
  const choices: Raw[] = (orderData?.pedidos ?? []).filter((o: Raw) => { const q = search.trim().toLowerCase(); return !q || `${o.id} ${o.vecino} ${o.zona}`.toLowerCase().includes(q); });
  const chosen = choices.some((o) => String(o.id) === draft.pedido) ? draft.pedido : String(choices[0]?.id ?? '');
  const open = async (event: FormEvent) => {
    event.preventDefault();
    if (!chosen) return;
    if (await run(() => api.post('/api/admin/incidencias', { ...draft, pedido: chosen }), `Incidencia del pedido ${chosen} registrada.`)) { setDraft({ pedido: '', tipo: 'ENTREGA', descripcion: '' }); setSearch(''); void reload(); }
  };
  const close = (id: number) => run(() => api.post(`/api/admin/incidencias/${id}/cerrar`, { nota: notes[id] ?? '' }), `Incidencia ${id} cerrada.`).then(() => reload());
  const kind = (value: string) => INCIDENT_KINDS.find((k) => k.value === value)?.label ?? value;
  const opened = data.incidencias.filter((i: Raw) => i.estado === 'ABIERTA');
  const closed = data.incidencias.filter((i: Raw) => i.estado !== 'ABIERTA');
  return (
    <>
      <Card eyebrow="No mueve dinero" title="Registrar una incidencia">
        <form className="buffer-form" onSubmit={open}>
          {orderData?.ciclos?.length ? <CycleSelect cycles={orderData.ciclos} value={orderData.ciclo} onChange={setWeek} /> : null}
          <label className="checkout-field"><span>Buscar el pedido</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Número, vecino o edificio" /></label>
          <label className="checkout-field"><span>Pedido</span><select value={chosen} onChange={(event) => setDraft({ ...draft, pedido: event.target.value })} required disabled={!choices.length}>{choices.length ? choices.map((o: Raw) => <option key={o.id} value={o.id}>Pedido {o.id} · {o.vecino} · {o.zona}</option>) : <option value="">Ningún pedido coincide</option>}</select></label>
          <div className="segmented">{INCIDENT_KINDS.map((k) => <button key={k.value} type="button" className={draft.tipo === k.value ? 'is-active' : ''} onClick={() => setDraft({ ...draft, tipo: k.value })}>{k.label}</button>)}</div>
          <label className="checkout-field"><span>Qué pasó</span><textarea value={draft.descripcion} onChange={(event) => setDraft({ ...draft, descripcion: event.target.value })} maxLength={500} rows={3} required /></label>
          <button className="primary-button" type="submit" disabled={!chosen}>Registrar</button>
          <small>Si hay que devolver dinero, va por un reclamo o una devolución.</small>
        </form>
      </Card>
      <Card title={`Abiertas (${opened.length})`}>
        {opened.length ? <div className="work-list">{opened.map((i: Raw) => (
          <article className="work-card" key={i.id}>
            <div className="work-card-top"><div className="claim-item"><span className="work-icon" aria-hidden="true"><Icon name="warning" size={20} /></span><div><strong>Pedido {i.pedido}</strong><span>{kind(i.tipo)}</span></div></div></div>
            <p className="work-text">{i.descripcion}</p>
            <AiDraft kind="incidencia" id={i.id} />
            <label className="checkout-field"><span>Qué se hizo</span><input value={notes[i.id] ?? ''} onChange={(event) => setNotes((n) => ({ ...n, [i.id]: event.target.value }))} placeholder="Ej. Llamé a la portería y avisó a la vecina" aria-label={`Nota para cerrar la incidencia ${i.id}`} /></label>
            <button className="primary-button" type="button" disabled={!notes[i.id]?.trim()} onClick={() => void close(i.id)}>Cerrar incidencia</button>
          </article>
        ))}</div> : <Empty icon="ok" title="Sin incidencias abiertas" text="Aquí quedan las que registres al atender a un vecino." />}
      </Card>
      {closed.length ? <Card title="Cerradas"><div className="work-list">{closed.map((i: Raw) => <article className="work-card work-card--done" key={i.id}><div className="work-card-top"><div className="claim-item"><div><strong>Pedido {i.pedido} · {kind(i.tipo)}</strong><span>{i.descripcion}</span></div></div><span className="state-pill state-pill--ok">Cerrada</span></div><p className="admin-muted">{i.nota}</p></article>)}</div></Card> : null}
    </>
  );
}

function Purchases({ cycle, setCycle, run, notify }: SectionProps) {
  const { data, reload } = useLoad<Raw>(`/api/compras${cycle ? `?ciclo=${cycle}` : ''}`, notify);
  const [add, setAdd] = useState({ producto: '', cantidad: '' });
  const [use, setUse] = useState({ faltante: '', cantidad: '' });
  const [freight, setFreight] = useState({ empresa: '', monto: '' });
  if (!data) return <AdminSkeleton />;
  const suppliers: Raw[] = data.proveedores;
  const registerFreight = async (event: FormEvent) => {
    event.preventDefault();
    if (await run(() => api.post('/api/compras/flete', { ciclo: data.ciclo, ...freight }), `Flete de ${freight.empresa} registrado.`)) void reload();
  };
  const total = suppliers.reduce((sum, p) => sum + num(p.total), 0);
  const buffer: Raw = data.colchon;
  const used = Math.min(100, (num(buffer.valor) / Math.max(num(buffer.tope), 1)) * 100);
  const partial = Boolean(data.parcial);
  const keepable: Raw[] = data.guardables ?? [];
  const keepChoice = add.producto || keepable[0]?.id || '';
  const nameOf = (id: string) => keepable.find((p) => p.id === id)?.nombre ?? buffer.stock.find((b: Raw) => b.producto === id)?.nombre ?? id;
  const addStock = async (event: FormEvent) => {
    event.preventDefault();
    if (await run(() => api.post('/api/compras/colchon', { ciclo: data.ciclo, producto: keepChoice, cantidad: add.cantidad }), `Se guardó ${add.cantidad} de ${nameOf(keepChoice)} en el colchón.`)) { setAdd({ producto: '', cantidad: '' }); void reload(); }
  };
  const real: Raw | null = data.compra_real;
  const ordered: Raw[] = suppliers.flatMap((p) => p.lineas);
  const registerPurchase = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const recibido: Record<string, string> = {};
    for (const l of ordered) { const got = String(form.get(l.producto) ?? '').trim(); if (got && got !== String(l.cantidad)) recibido[l.producto] = got; } // CR-04: solo lo que faltó
    if (await run(() => api.post('/api/compras/recibido', { ciclo: data.ciclo, recibido }), Object.keys(recibido).length ? 'Compra registrada: lo que faltó se repone con el colchón o se devuelve a los vecinos.' : 'Compra registrada: llegó todo.')) void reload();
  };
  // S-329: reponer desde el faltante, solo si el colchón tiene ese producto
  const inStock = (id: string) => buffer.stock.some((b: Raw) => b.producto === id && num(b.cantidad) > 0);
  const coverable: Raw[] = (real?.faltantes ?? []).map((f: Raw, i: number) => ({ ...f, key: String(i) })).filter((f: Raw) => num(f.cantidad) > num(f.colchon) && inStock(f.producto));
  const useChoice = coverable.find((f) => f.key === use.faltante) ?? coverable[0];
  const useStock = async (event: FormEvent) => {
    event.preventDefault();
    if (!useChoice) return;
    if (await run(() => api.post('/api/compras/colchon/usar', { pedido: String(useChoice.pedido), producto: useChoice.producto, cantidad: use.cantidad }), `Se repuso ${use.cantidad} de ${useChoice.nombre ?? useChoice.producto} al pedido ${useChoice.pedido}.`)) { setUse({ faltante: '', cantidad: '' }); void reload(); }
  };
  return (
    <>
      <section className="admin-intro"><div><h2>Lo que hay que comprar</h2><p>{partial ? 'Los pedidos siguen abiertos hasta el miércoles a las 20:00: las cantidades todavía pueden subir.' : 'Cantidades finales: solo cuentan los pedidos de grupos que llegaron al mínimo.'}</p></div><CycleSelect cycles={data.ciclos} value={data.ciclo} onChange={setCycle} /></section>
      <div className="purchase-stats">
        <div className="purchase-stat"><span>Proveedores</span><strong>{suppliers.length}</strong></div>
        <div className="purchase-stat"><span>Total a pagar</span><strong>{formatMoney(total)}</strong></div>
        <div className="purchase-stat"><span>Estado</span><strong>{partial ? <span className="state-pill">Abierto</span> : <span className="state-pill state-pill--ok">Cerrado</span>}</strong></div>
      </div>
      {suppliers.length ? suppliers.map((p) => (
        <Card key={p.id} title={p.nombre} aside={<strong className="purchase-total">{formatMoney(num(p.total))}</strong>}>
          <ul className="buy-lines">{p.lineas.map((l: Raw) => <li key={l.producto}><ProductThumb id={l.producto} size={44} /><div><strong>{l.nombre}</strong><span>{formatMoney(num(l.precio))} por {l.unidad}{l.desde !== '0' ? ` · precio desde ${l.desde} ${l.unidad}` : ''}</span></div><div className="buy-line-amount"><strong>{quantityWithUnit(l.cantidad, l.unidad)}</strong><span>{formatMoney(num(l.monto))}</span></div></li>)}</ul>
        </Card>
      )) : <Card title="Sin compras esta semana"><Empty icon="cart" title="Todavía no hay nada que comprar" text="Aparece cuando hay pedidos de grupos que llegan al mínimo." /></Card>}
      {!partial && ordered.length ? <Card eyebrow="Después de recibir al proveedor" title={real ? 'Compra registrada' : 'Lo que llegó'}>
        {real ? (real.faltantes.length
          ? <ul className="buy-lines">{real.faltantes.map((f: Raw, i: number) => <li key={i}><ProductThumb id={f.producto} size={44} /><div><strong>{f.nombre ?? f.producto}</strong><span>Pedido {f.pedido} · {f.origen === 'DANADO' ? 'dañado al armar' : 'faltó en la compra'}{num(f.colchon) > 0 ? ` · el colchón repuso ${f.colchon}` : ''}</span></div><div className="buy-line-amount"><strong>Faltó {f.cantidad}</strong></div></li>)}</ul>
          : <p className="admin-muted">Llegó todo. El reparto ya puede salir.</p>)
          : <form onSubmit={registerPurchase}><p className="admin-muted">Corrige solo lo que llegó de menos. Lo que falte se repone primero con el colchón y el resto se descuenta a los últimos pedidos, que lo reciben de vuelta como saldo. El reparto no sale hasta registrar esto.</p>
            <ul className="buy-lines">{ordered.map((l) => <li key={l.producto}><ProductThumb id={l.producto} size={44} /><div><strong>{l.nombre}</strong><span>Pedido: {quantityWithUnit(l.cantidad, l.unidad)}</span></div><label className="buy-line-input"><span className="sr-only">Cuánto llegó de {l.nombre}</span><input className="admin-inline-input" name={l.producto} defaultValue={l.cantidad} inputMode="decimal" aria-label={`Cuánto llegó de ${l.nombre}`} /><small>{l.unidad}</small></label></li>)}</ul>
            <button className="primary-button" type="submit">Registrar la compra</button></form>}
      </Card> : null}
      {!partial && ordered.length ? <Card eyebrow="Lo paga Yapa: el proveedor no entrega" title="Flete de la compra">
        {data.flete ? <p className="admin-muted"><strong>{data.flete.empresa}</strong> · {formatMoney(num(data.flete.monto))}. Se reparte entre los pedidos de la semana en el margen real.</p>
          : <form className="buffer-form" onSubmit={registerFreight}><p className="admin-muted">Registra lo que pagaste por traer la compra del mercado. Sin esto, las métricas estiman S/ 180.</p>
            <label className="checkout-field"><span>Empresa</span><input value={freight.empresa} onChange={(event) => setFreight({ ...freight, empresa: event.target.value })} maxLength={80} placeholder="Fletes Santa Anita" required /></label>
            <label className="checkout-field"><span>Monto (S/)</span><input value={freight.monto} onChange={(event) => setFreight({ ...freight, monto: event.target.value })} inputMode="decimal" placeholder="120.00" required /></label>
            <button className="primary-button" type="submit">Registrar flete</button></form>}
      </Card> : null}
      <Card eyebrow="Colchón de reposición" title={`${formatMoney(num(buffer.valor))} de ${formatMoney(num(buffer.tope))}`}>
        <div className="buffer-meter" role="meter" aria-valuemin={0} aria-valuemax={num(buffer.tope)} aria-valuenow={num(buffer.valor)} aria-label="Valor guardado en el colchón"><span style={{ width: `${used}%` }} /></div>
        {buffer.stock.length ? <ul className="buy-lines">{buffer.stock.map((b: Raw) => <li key={b.producto}><ProductThumb id={b.producto} size={44} /><div><strong>{b.nombre ?? b.producto}</strong><span>{formatMoney(num(b.valor))}</span></div><div className="buy-line-amount"><strong>{b.cantidad}</strong></div></li>)}</ul> : <p className="admin-muted">El colchón está vacío. Solo se guardan productos de limpieza, que no se malogran.</p>}
        <div className="buffer-forms">
          <form className="buffer-form" onSubmit={addStock}><h3>Guardar en el colchón</h3>
            <label className="checkout-field"><span>Producto</span><select value={keepChoice} onChange={(event) => setAdd({ ...add, producto: event.target.value })} required disabled={!keepable.length}>{keepable.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}</select></label>
            <label className="checkout-field"><span>Cantidad</span><input value={add.cantidad} onChange={(event) => setAdd({ ...add, cantidad: event.target.value })} inputMode="decimal" placeholder="2" required /></label>
            <button className="primary-button" type="submit" disabled={!keepChoice}>Guardar</button>
          </form>
          <form className="buffer-form" onSubmit={useStock}><h3>Reponer un faltante</h3>
            {coverable.length ? <>
              <label className="checkout-field"><span>Faltante</span><select value={useChoice?.key ?? ''} onChange={(event) => setUse({ ...use, faltante: event.target.value })}>{coverable.map((f) => <option key={f.key} value={f.key}>Pedido {f.pedido} · {f.nombre ?? f.producto} · faltó {f.cantidad}</option>)}</select></label>
              <label className="checkout-field"><span>Cantidad</span><input value={use.cantidad} onChange={(event) => setUse({ ...use, cantidad: event.target.value })} inputMode="decimal" placeholder="1" required /></label>
              <button className="admin-row-button" type="submit">Reponer</button>
            </> : <p className="admin-muted">Aquí aparecen los faltantes de la semana que el colchón puede cubrir.</p>}
          </form>
        </div>
      </Card>
    </>
  );
}

// iteración 55: los seis tipos de cuenta que crea el admin (S-278, S-289)
const ACCOUNT_KINDS: Array<{ id: Role; icon: IconName; does: string; example: string }> = [
  { id: 'armador', icon: 'box', does: 'Arma las bolsas con su foto', example: 'armado-1' },
  { id: 'compras', icon: 'cart', does: 'Compra y maneja el colchón', example: 'compras-1' },
  { id: 'atencion', icon: 'headset', does: 'Reclamos, devoluciones y PIN', example: 'atencion-1' },
  { id: 'porteria', icon: 'building', does: 'Recibe las bolsas en su edificio', example: 'porteria-alamos' },
  { id: 'transportista', icon: 'truck', does: 'Entrega los sábados', example: 'reparto-1' },
  { id: 'proveedor', icon: 'store', does: 'Manda su lista semanal', example: 'mercado-norte' },
];

function Partners({ run, notify }: SectionProps) {
  const { data, reload } = useLoad<Raw>('/api/admin/cuentas', notify);
  const { data: offerData, reload: reloadOffers } = useLoad<Raw>('/api/admin/propuestas', notify);
  const [form, setForm] = useState({ tipo: 'armador', usuario: '', nombre: '', proveedor: '', zona: '', contrasena: '' });
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [editing, setEditing] = useState<{ user: string; password: string } | null>(null);
  if (!data || !offerData) return <AdminSkeleton />;
  const supplier = form.tipo === 'proveedor';
  const concierge = form.tipo === 'porteria';
  const kind = ACCOUNT_KINDS.find((k) => k.id === form.tipo)!;
  const create = async (event: FormEvent) => {
    event.preventDefault();
    // un proveedor nuevo toma su código del usuario (S-283)
    const body = form.proveedor === 'nuevo' ? { ...form, proveedor: `SUP-${form.usuario.toUpperCase()}` } : form;
    const ok = await run(() => api.post('/api/admin/cuentas', body), `Cuenta ${form.usuario} creada. Pásale su usuario y contraseña por un canal privado.`);
    if (ok) { setForm({ ...form, usuario: '', nombre: '', proveedor: '', zona: '', contrasena: '' }); void reload(); }
  };
  const savePassword = async (event: FormEvent) => {
    event.preventDefault();
    if (!editing) return;
    const ok = await run(() => api.post(`/api/admin/cuentas/${editing.user}/contrasena`, { contrasena: editing.password }), `${editing.user} ya puede entrar con su contraseña nueva.`);
    if (ok) { setEditing(null); void reload(); }
  };
  const offerKey = (o: Raw) => `${o.ciclo}/${o.proveedor}`;
  const review = (o: Raw, decision: 'aprobar' | 'rechazar') => run(() => api.post(`/api/admin/propuestas/${o.ciclo}/${o.proveedor}/${decision}`, decision === 'rechazar' ? { motivo: reasons[offerKey(o)] ?? '' } : {}),
    decision === 'aprobar' ? `Lista de ${o.nombre_proveedor} publicada para el ${weekRangeLabel(o.ciclo)}.` : `Lista devuelta a ${o.nombre_proveedor} con tu motivo.`).then(() => reloadOffers());
  return (
    <>
      <Card title={`Listas de proveedores (${offerData.propuestas.length})`}>
        {offerData.propuestas.length ? <div className="offer-list">{offerData.propuestas.map((o: Raw) => (
          <article className="offer-card" key={offerKey(o)}>
            <div className="stop-head"><strong>{o.nombre_proveedor}</strong><span>{weekRangeLabel(o.ciclo)}</span><span className={`state-pill ${o.estado === 'APROBADA' ? 'state-pill--ok' : o.estado === 'RECHAZADA' ? 'state-pill--bad' : ''}`}>{OFFER_STATES[o.estado]}</span></div>
            <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Producto</th><th>Máximo</th><th>Tramos</th></tr></thead><tbody>{o.productos.map((p: Raw) => <tr key={p.id}><td><span className="cell-with-thumb"><ProductThumb id={p.id} size={32} />{p.nombre}</span></td><td>{p.maximo} {p.unidad}</td><td><small>{p.tramos.map((t: Raw) => `desde ${t.desde}: ${formatMoney(num(t.precio))}`).join(' · ')}</small></td></tr>)}</tbody></table></div>
            {o.motivo ? <p className="admin-muted">Motivo: {o.motivo}</p> : null}
            {o.estado === 'PENDIENTE' ? <div className="offer-actions">
              <ConfirmAction label="Aprobar y publicar" question="Sus productos de esa semana se reemplazan por esta lista. ¿Publicar?" confirmLabel="Publicar" onConfirm={() => review(o, 'aprobar')} />
              <label className="checkout-field"><span>Motivo para devolverla</span><input value={reasons[offerKey(o)] ?? ''} onChange={(event) => setReasons({ ...reasons, [offerKey(o)]: event.target.value })} placeholder="Ej.: falta la cebolla" /></label>
              <button className="admin-row-button" type="button" onClick={() => void review(o, 'rechazar')}>Devolver</button>
            </div> : null}
          </article>
        ))}</div> : <Empty icon="store" title="No hay listas" text="Cuando un proveedor mande su lista de la semana, aparece aquí para que la revises." />}
      </Card>
      <form className="admin-card" onSubmit={create}><div className="admin-card-heading"><div><span className="admin-eyebrow">Solo el admin crea cuentas</span><h2>Crear una cuenta</h2></div></div>
        <div className="role-picker" role="radiogroup" aria-label="Tipo de cuenta">{ACCOUNT_KINDS.map((k) => <label key={k.id} className={`role-option ${form.tipo === k.id ? 'is-selected' : ''}`}><input type="radio" name="tipo-cuenta" value={k.id} checked={form.tipo === k.id} onChange={() => setForm({ ...form, tipo: k.id, proveedor: '', zona: '' })} /><Icon name={k.icon} size={20} /><span><strong>{ROLE_LABELS[k.id]}</strong><small>{k.does}</small></span></label>)}</div>
        <div className="form-grid">
          <label className="checkout-field"><span>Usuario</span><input value={form.usuario} onChange={(event) => setForm({ ...form, usuario: event.target.value.toLowerCase() })} placeholder={kind.example} autoCapitalize="none" spellCheck={false} required /></label>
          {concierge ? <label className="checkout-field"><span>Zona que recibe</span><select value={form.zona} onChange={(event) => setForm({ ...form, zona: event.target.value })} required><option value="">Elige…</option>{data.zonas.map((z: Raw) => <option key={z.id} value={z.id}>{z.nombre} · {z.distrito}</option>)}</select></label> : null}
          {supplier ? <label className="checkout-field"><span>Proveedor</span><select value={form.proveedor} onChange={(event) => setForm({ ...form, proveedor: event.target.value })} required><option value="">Elige…</option>{data.proveedores.map((p: Raw) => <option key={p.id} value={p.id}>{p.nombre}</option>)}<option value="nuevo">Otro proveedor (nuevo)</option></select></label> : null}
          {!supplier || form.proveedor === 'nuevo' ? <label className="checkout-field"><span>{supplier ? 'Nombre del proveedor' : concierge ? 'Nombre (conserje o encargado)' : 'Nombre'}</span><input value={form.nombre} onChange={(event) => setForm({ ...form, nombre: event.target.value })} required /></label> : null}
          <label className="checkout-field"><span>Contraseña (10 o más caracteres)</span><input type="text" value={form.contrasena} onChange={(event) => setForm({ ...form, contrasena: event.target.value })} minLength={10} autoComplete="off" required /></label>
        </div>
        <button className="primary-button" type="submit">Crear cuenta</button>
      </form>
      <Card title={`Cuentas (${data.cuentas.length})`}>
        {data.cuentas.length ? <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Usuario</th><th>Rol</th><th>Estado</th><th><span className="sr-only">Acciones</span></th></tr></thead><tbody>{data.cuentas.map((c: Raw) => <tr key={c.usuario}>
          <td><strong>{c.usuario}</strong><small className="admin-cell-note">{c.nombre}</small></td>
          <td>{ROLE_LABELS[c.tipo as Role] ?? c.tipo}{c.zona ? <small className="admin-cell-note">{data.zonas.find((z: Raw) => z.id === c.zona)?.nombre ?? c.zona}</small> : null}</td>
          <td>{c.activa ? <span className="state-pill state-pill--ok">Activa</span> : <span className="state-pill state-pill--bad">Desactivada</span>}</td>
          <td className="admin-row-actions">{c.activa ? <ConfirmAction label="Desactivar" question={`${c.usuario} no podrá entrar. ¿Desactivar?`} confirmLabel="Desactivar" onConfirm={() => run(() => api.post(`/api/admin/cuentas/${c.usuario}/desactivar`), `${c.usuario} ya no puede entrar.`).then(() => reload())} /> : null}{editing?.user === c.usuario
            ? <form className="inline-form" onSubmit={savePassword}><label><span className="sr-only">Contraseña nueva</span><input value={editing?.password ?? ''} onChange={(event) => setEditing({ user: c.usuario, password: event.target.value })} minLength={10} placeholder="10 o más caracteres" autoComplete="off" autoFocus required /></label><button className="admin-row-button" type="submit">Guardar</button><button className="admin-row-button" type="button" onClick={() => setEditing(null)}>Cancelar</button></form>
            : <button className="admin-row-button" type="button" onClick={() => setEditing({ user: c.usuario, password: '' })}>{c.activa ? 'Nueva contraseña' : 'Reactivar'}</button>}</td>
        </tr>)}</tbody></table></div> : <Empty icon="users" title="Sin cuentas todavía" text="Crea una para cada persona del equipo, cada portería, cada transportista y cada proveedor aliado." />}
      </Card>
    </>
  );
}

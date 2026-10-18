import { useMemo, useState } from 'react';
import type { FormEvent } from 'react';
import type { Zone } from '../types';
import { Icon } from './Icon';
import { shareText } from './AuthDialog';
import { ConfirmAction } from './ConfirmAction';
import { ZonesMap, type MapUnion, type MapZone } from './ZonesMap';
import { unionReason } from '../utils/zoneMap';

export interface ZonePanel extends Zone {
  progress: { verified: number; minimum: number; cycle: string };
  neighborsList: Array<{ id: number; name: string; ordered: boolean }>;
  nearby: Array<Zone & { distance: number; sameGroup: boolean; reason: string }>;
  requests: Array<{ id: number; zone: string; name: string }>;
  benefits: { freeDelivery: boolean; discountPct: number; discountActive: boolean; discountUntil: string | null };
  referralCode: string;
}

export interface MyZone {
  zone: Zone | null;
  admin: ZonePanel | null;
  referralCode: string;
  radius: number;
  mergeDistance: number;
}

interface ZonePageProps {
  data: MyZone | null;
  zones: Zone[];
  userId: number;
  districts: string[];
  onBack: () => void;
  onJoin: (zoneId: string) => Promise<void>;
  onLocate: (lat: number, lon: number) => Promise<void>;
  onCreate: (name: string, district: string, lat: number, lon: number) => Promise<void>;
  onActivate: (zoneId: string, kind: string, contact: string) => Promise<void>;
  onRequestMerge: (zoneId: string, target: string) => Promise<void>;
  onAnswerMerge: (requestId: number, accept: boolean) => Promise<void>;
  onLeaveGroup: (zoneId: string) => Promise<void>;
  onTransfer: (zoneId: string, newAdmin: number) => Promise<void>;
}

const RECEPTION = [{ value: 'PORTERIA', label: 'La portería' }, { value: 'ENCARGADO', label: 'Un encargado' }, { value: 'ADMIN', label: 'Yo mismo' }];
const reminder = (cycle: string) => `¡Hola, vecino! Esta semana (${cycle}) compramos juntos en Yapa. Si llegamos a 8 pedidos verificados, el camión viene el sábado y todos ahorramos. Pide antes del miércoles 20:00.`;

function ShareCard({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <section className="customer-side-card referral-side">
      <span className="customer-eyebrow"><Icon name="gift" size={14} /> Invita y gana</span>
      <h2>Tu código: <span className="code-chip">{code}</span></h2>
      <p>Cuando tu invitado recibe su primer pedido, <strong>los dos ganan S/ 3 de saldo</strong>.</p>
      <div className="share-actions">
        <a className="primary-button" href={`https://wa.me/?text=${encodeURIComponent(shareText(code))}`} target="_blank" rel="noreferrer"><Icon name="whatsapp" size={18} /> Compartir por WhatsApp</a>
        <button className="secondary-button" type="button" onClick={() => { void navigator.clipboard?.writeText(code).then(() => setCopied(true)); }}><Icon name={copied ? 'check' : 'copy'} size={16} /> {copied ? 'Copiado' : 'Copiar código'}</button>
      </div>
    </section>
  );
}

function ProgressRing({ value, total }: { value: number; total: number }) {
  const ratio = Math.min(value / total, 1);
  const circumference = 2 * Math.PI * 52;
  return (
    <svg className="progress-ring" viewBox="0 0 120 120" role="img" aria-label={`${value} de ${total} pedidos verificados`}>
      <circle cx="60" cy="60" r="52" className="progress-ring-track" />
      <circle cx="60" cy="60" r="52" className={`progress-ring-value ${ratio >= 1 ? 'is-ready' : ''}`} strokeDasharray={`${circumference * ratio} ${circumference}`} transform="rotate(-90 60 60)" />
      <text x="60" y="58" className="progress-ring-number">{value}/{total}</text>
      <text x="60" y="78" className="progress-ring-label">verificados</text>
    </svg>
  );
}

function AdminPanel({ panel, data, userId, ...actions }: { panel: ZonePanel; data: MyZone; userId: number } & Pick<ZonePageProps, 'onActivate' | 'onRequestMerge' | 'onAnswerMerge' | 'onLeaveGroup' | 'onTransfer'>) {
  const [kind, setKind] = useState('PORTERIA');
  const [contact, setContact] = useState('');
  const [newAdmin, setNewAdmin] = useState<number | ''>('');
  const [confirmTransfer, setConfirmTransfer] = useState(false);
  const missing = Math.max(panel.progress.minimum - panel.progress.verified, 0);
  const others = panel.neighborsList.filter((n) => n.id !== userId);
  const sharesGroup = panel.nearby.some((z) => z.sameGroup);
  const mapZones = useMemo<MapZone[]>(() => [panel, ...panel.nearby].map((zone) => ({ id: zone.id, name: zone.name, group: zone.group, lat: zone.lat, lon: zone.lon })), [panel]);
  const mapUnions = useMemo<MapUnion[]>(() => panel.nearby.filter((zone) => !zone.sameGroup).map((zone) => ({ a: panel.id, b: zone.id, distance: zone.distance, reason: zone.reason })), [panel]);

  return (
    <>
      <section className="zone-hero">
        <div className="zone-hero-copy">
          <span className="role-badge role-badge--admin_zona"><Icon name="crown" size={14} /> Admin de zona</span>
          <h1>{panel.name}</h1>
          <p>{panel.district} · {panel.neighbors} vecinos · {panel.status === 'ACTIVA' ? `recibe ${panel.contact || 'la portería'}` : 'falta definir quién recibe'}</p>
          <p className="zone-hero-message">{missing ? <>Faltan <strong>{missing} pedidos verificados</strong> para que el camión venga el sábado.</> : <><Icon name="confetti" size={18} /> <strong>¡Llegaron al mínimo!</strong> El sábado entregamos en tu edificio.</>}</p>
        </div>
        <ProgressRing value={panel.progress.verified} total={panel.progress.minimum} />
      </section>

      {panel.status !== 'ACTIVA' ? (
        <form className="customer-main-card activate-card" onSubmit={(event: FormEvent) => { event.preventDefault(); void actions.onActivate(panel.id, kind, contact); }}>
          <h2><Icon name="warning" size={20} /> Activa tu zona</h2><p>Tu zona recibe pedidos cuando alguien acepta recibirlos el sábado.</p>
          <div className="segmented" role="radiogroup" aria-label="Quién recibe">{RECEPTION.map((r) => <button type="button" key={r.value} role="radio" aria-checked={kind === r.value} className={kind === r.value ? 'is-active' : ''} onClick={() => setKind(r.value)}>{r.label}</button>)}</div>
          <label className="checkout-field"><span>Nombre de quien recibe</span><input value={contact} onChange={(event) => setContact(event.target.value)} placeholder="Ej. Sr. Ramos, portero" required /></label>
          <button className="primary-button" type="submit">Activar zona</button>
        </form>
      ) : null}

      <div className="zone-grid">
        <section className="customer-main-card">
          <div className="customer-section-heading"><div><span className="customer-eyebrow">Semana {panel.progress.cycle}</span><h2>Tus vecinos</h2></div><span className="customer-count">{panel.neighborsList.filter((n) => n.ordered).length} de {panel.neighborsList.length} pidieron</span></div>
          <table className="zone-table"><tbody>{panel.neighborsList.map((n) => <tr key={n.id}><td><span className="avatar-dot">{n.name[0]}</span>{n.name}{n.id === userId ? <small> (tú)</small> : null}</td><td>{n.ordered ? <span className="state-pill state-pill--ok"><Icon name="check" size={13} /> Ya pidió</span> : <span className="state-pill">Aún no</span>}</td></tr>)}</tbody></table>
          <a className="secondary-button" href={`https://wa.me/?text=${encodeURIComponent(reminder(panel.progress.cycle))}`} target="_blank" rel="noreferrer"><Icon name="whatsapp" size={17} /> Recordar al grupo del edificio</a>
          <p className="admin-muted">Ves los nombres y si ya pidieron; los montos y las direcciones de tus vecinos son privados.</p>
        </section>

        <section className="customer-main-card">
          <div className="customer-section-heading"><div><h2>Radio y zonas cercanas</h2></div></div>
          <ZonesMap zones={mapZones} unions={mapUnions} radius={data.radius} mergeDistance={data.mergeDistance} highlightId={panel.id} label={`Mapa de ${panel.name}: radio de ${data.radius} metros y zonas cercanas`} />
          {panel.nearby.length ? <table className="zone-table"><tbody>{panel.nearby.map((z) => <tr key={z.id}><td><strong>{z.name}</strong><small> · {z.distance} m</small></td><td>{z.sameGroup ? <span className="state-pill state-pill--ok"><Icon name="merge" size={13} /> Unidas</span> : z.reason ? <span className="merge-blocked">{unionReason(z.reason)}</span> : <ConfirmAction label="Pedir unión" confirmLabel="Sí, pedir unión" question={<>Si {z.name} acepta, sus pedidos y los tuyos suman juntos para llegar al mínimo. ¿Pedir unión?</>} onConfirm={() => actions.onRequestMerge(panel.id, z.id)} />}</td></tr>)}</tbody></table> : <p className="admin-muted">No hay zonas a {data.mergeDistance} m o menos para unir.</p>}
          {panel.requests.length ? <div className="merge-requests"><strong>Solicitudes para unirse contigo</strong>{panel.requests.map((r) => <div className="merge-request" key={r.id}><span>{r.name}</span><button className="admin-row-button" type="button" onClick={() => void actions.onAnswerMerge(r.id, true)}>Aceptar</button><button className="text-button" type="button" onClick={() => void actions.onAnswerMerge(r.id, false)}>Rechazar</button></div>)}</div> : null}
          {sharesGroup ? <ConfirmAction label="Separar mi zona del grupo" className="text-button" confirmLabel="Sí, separar" question={<>Tu zona volverá a contar sola para el mínimo. ¿Separar?</>} onConfirm={() => actions.onLeaveGroup(panel.id)} /> : null}
          <p className="admin-muted">Unidas, dos zonas suman sus pedidos para llegar al mínimo, y el camión hace dos paradas cortas.</p>
        </section>
      </div>

      <section className="benefit-row" aria-label="Tus beneficios">
        <div className={`benefit-card ${panel.benefits.freeDelivery ? 'is-on' : ''}`}><Icon name="truck" size={26} weight="duotone" /><strong>Envío gratis</strong><span>Cada semana que tu zona se atiende</span></div>
        <div className={`benefit-card ${panel.benefits.discountActive ? 'is-on' : ''}`}><Icon name="percent" size={26} weight="duotone" /><strong>{panel.benefits.discountPct} % de descuento</strong><span>{panel.benefits.discountActive ? `Hasta la semana ${panel.benefits.discountUntil}` : 'Las primeras 4 semanas de tu zona'}</span></div>
        <div className="benefit-card is-on"><Icon name="gift" size={26} weight="duotone" /><strong>S/ 3 por vecino invitado</strong><span>Para ti y para él, con su primer pedido</span></div>
      </section>

      <div className="zone-grid">
        <ShareCard code={panel.referralCode} />
        <section className="customer-side-card">
          <span className="customer-eyebrow"><Icon name="switch" size={14} /> Pasar la posta</span><h2>Transferir el rol de admin</h2>
          <p>Si te mudas o ya no puedes organizar, elige a un vecino de tu zona.</p>
          <label className="checkout-field"><span>Nuevo admin</span><select value={newAdmin} onChange={(event) => { setNewAdmin(event.target.value ? Number(event.target.value) : ''); setConfirmTransfer(false); }}><option value="">Elige un vecino</option>{others.map((n) => <option key={n.id} value={n.id}>{n.name}</option>)}</select></label>
          {confirmTransfer && newAdmin ? <div className="admin-settle-actions"><button className="primary-button" type="button" onClick={() => void actions.onTransfer(panel.id, Number(newAdmin))}>Sí, transferir</button><button className="secondary-button" type="button" onClick={() => setConfirmTransfer(false)}>Cancelar</button></div> : <button className="secondary-button" type="button" disabled={!newAdmin} onClick={() => setConfirmTransfer(true)}>Transferir</button>}
        </section>
      </div>
    </>
  );
}

function NeighborView({ data, zones, districts, onJoin, onLocate, onCreate }: { data: MyZone; zones: Zone[]; districts: string[] } & Pick<ZonePageProps, 'onJoin' | 'onLocate' | 'onCreate'>) {
  const [target, setTarget] = useState('');
  const [name, setName] = useState('');
  const [district, setDistrict] = useState(districts[0] ?? '');
  const [spot, setSpot] = useState<{ lat: number; lon: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [locError, setLocError] = useState('');
  const options = zones.filter((z) => z.id !== data.zone?.id && z.status === 'ACTIVA' && districts.includes(z.district));

  const locate = () => {
    if (!navigator.geolocation) { setLocError('Tu navegador no comparte la ubicación.'); return; }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(async (position) => {
      const next = { lat: Number(position.coords.latitude.toFixed(5)), lon: Number(position.coords.longitude.toFixed(5)) };
      try {
        await onLocate(next.lat, next.lon);
        setSpot(next);
        setLocError('');
      } finally {
        setLocating(false);
      }
    }, () => { setLocating(false); setLocError('No pudimos leer tu ubicación. Revisa el permiso del navegador.'); });
  };

  return (
    <>
      <section className="zone-hero">
        <div className="zone-hero-copy">
          
          <h1>{data.zone?.name ?? 'Todavía no tienes zona'}</h1>
          <p>{data.zone ? `${data.zone.district} · ${data.zone.neighbors} vecinos · ${data.zone.status === 'ACTIVA' ? 'recibe pedidos' : 'falta quien reciba'}` : 'Únete a la zona de tu edificio o crea una.'}</p>
        </div>
        <span className="zone-hero-icon"><Icon name="map" size={46} weight="duotone" /></span>
      </section>
      <div className="zone-grid">
        <section className="customer-main-card">
          <h2><Icon name="pin" size={20} /> Tu ubicación</h2>
          <p>Para unirte o crear una zona necesitamos saber dónde vives. Solo la usa Yapa para el radio de 300 m.</p>
          <button className="secondary-button" type="button" onClick={locate} disabled={locating}><Icon name="pin" size={17} /> {locating ? 'Buscando…' : spot ? 'Ubicación guardada ✓' : 'Usar mi ubicación'}</button>
          {locError ? <p className="auth-feedback auth-feedback--error">{locError}</p> : null}
          <h2 className="zone-subtitle">Unirme a otra zona</h2>
          <div className="dos-columnas"><select value={target} onChange={(event) => setTarget(event.target.value)} aria-label="Zona"><option value="">Elige una zona</option>{options.map((z) => <option key={z.id} value={z.id}>{z.name} · {z.district}</option>)}</select><button className="primary-button" type="button" disabled={!target} onClick={() => void onJoin(target)}>Unirme</button></div>
        </section>
        <form className="customer-main-card" onSubmit={(event: FormEvent) => { event.preventDefault(); if (spot) void onCreate(name.trim(), district, spot.lat, spot.lon); }}>
          <h2><Icon name="crown" size={20} /> Organiza tu edificio</h2>
          <p>Si tu edificio todavía no tiene zona, créala. Serás su admin: <strong>envío gratis</strong>, <strong>5 % de descuento</strong> las primeras 4 semanas y <strong>S/ 3</strong> por cada vecino que invites.</p>
          <label className="checkout-field"><span>Nombre del edificio o condominio</span><input value={name} onChange={(event) => setName(event.target.value)} placeholder="Ej. Residencial Los Pinos" required /></label>
          <div className="segmented" role="radiogroup" aria-label="Distrito">{districts.map((d) => <button type="button" key={d} role="radio" aria-checked={district === d} className={district === d ? 'is-active' : ''} onClick={() => setDistrict(d)}>{d}</button>)}</div>
          <button className="primary-button" type="submit" disabled={!spot || !name.trim()}>{spot ? 'Crear mi zona' : 'Primero usa tu ubicación'}</button>
        </form>
      </div>
      <ShareCard code={data.referralCode} />
    </>
  );
}

export function ZonePage(props: ZonePageProps) {
  const { data } = props;
  return (
    <main className="customer-page" id="zone-page">
      {!data ? <p className="admin-muted">Cargando tu zona…</p> : data.admin ? <AdminPanel panel={data.admin} data={data} userId={props.userId} onActivate={props.onActivate} onRequestMerge={props.onRequestMerge} onAnswerMerge={props.onAnswerMerge} onLeaveGroup={props.onLeaveGroup} onTransfer={props.onTransfer} /> : <NeighborView data={data} zones={props.zones} districts={props.districts} onJoin={props.onJoin} onLocate={props.onLocate} onCreate={props.onCreate} />}
      <button className="text-button zone-back" type="button" onClick={props.onBack}><Icon name="arrow" size={16} /> Volver a la tienda</button>
    </main>
  );
}

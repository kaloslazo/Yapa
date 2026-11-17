import { useEffect, useMemo, useRef, useState } from 'react';
import { api } from '../services/api';
import { hasCoordinates, isPending, planDelivery, type RouteStop } from '../utils/deliveryRoute';
import { LazyRouteMap } from './LazyRouteMap';
import { Icon } from './Icon';
import './RoutePlanner.css';

export function RoutePlanner({ stops, active, onOrder, cycle }: { stops: RouteStop[]; active: boolean; onOrder: (ids: string[] | null) => void; cycle?: string }) {
  const [start, setStart] = useState('');
  const [road,setRoad]=useState<{distancia_m:number;duracion_s:number;coordenadas:Array<[number,number]>}|null>(null);
  const [busy,setBusy]=useState(false),[routeError,setRouteError]=useState('');
  const requestVersion=useRef(0);
  const plan = useMemo(() => planDelivery(stops, start), [stops, start]);
  const shown = plan.route;
  const points = useMemo(() => shown.map(s => ({ id: s.zona.id, name: s.zona.nombre, lat: s.zona.lat!, lon: s.zona.lon!, orders: s.pedidos.length })), [shown]);
  const routeKey=points.map(p=>`${p.id}:${p.lat}:${p.lon}`).join('|');
  useEffect(()=>{requestVersion.current++;setRoad(null);setRouteError('');setBusy(false);return()=>{requestVersion.current++;};},[routeKey,cycle]);
  const trace=async()=>{
    const request=++requestVersion.current;setBusy(true);setRouteError('');
    try { const result=await api.post<{distancia_m:number;duracion_s:number;coordenadas:Array<[number,number]>}>('/api/reparto/ruta',{ciclo:cycle,zonas:JSON.stringify(points.map(p=>p.id))}); if(request===requestVersion.current)setRoad(result); }
    catch(error){if(request===requestVersion.current){setRoad(null);setRouteError(error instanceof Error?error.message:'No pudimos trazar por calles.');}}
    finally{if(request===requestVersion.current)setBusy(false);}
  };
  // la ruta completa en Google Maps (sin clave): sale desde donde está el transportista, con las paradas en este orden
  const google = shown.length ? `https://www.google.com/maps/dir/?api=1&travelmode=driving&destination=${points[points.length - 1].lat},${points[points.length - 1].lon}${points.length > 1 ? `&waypoints=${encodeURIComponent(points.slice(0, -1).map(p => `${p.lat},${p.lon}`).join('|'))}` : ''}` : '';
  const lats = shown.map(s => s.zona.lat!), lons = shown.map(s => s.zona.lon!);
  const latSpan = Math.max(0.002, Math.max(...lats) - Math.min(...lats));
  const lonSpan = Math.max(0.002, Math.max(...lons) - Math.min(...lons));
  // Proyección local con escala igual en ambos ejes (distancias pequeñas en Lima).
  const cos = Math.cos((lats[0] ?? -12) * Math.PI / 180);
  const scale = Math.min(320 / (lonSpan * cos), 190 / latSpan);
  const x = (s: RouteStop) => 40 + (s.zona.lon! - Math.min(...lons)) * cos * scale;
  const y = (s: RouteStop) => 35 + (Math.max(...lats) - s.zona.lat!) * scale;
  const km = (n: number) => (n / 1000).toFixed(2);
  const pending = stops.filter(isPending).length;
  if (!pending) return null; // sin paradas pendientes no hay nada que ordenar
  const saved = plan.originalMeters - plan.proposedMeters;
  return <section className="route-planner" aria-labelledby="route-planner-title">
    <div className="route-planner-head">
      <div><h2 id="route-planner-title">Organiza tus paradas</h2><p>{plan.orders} pedidos en {pending} {pending === 1 ? 'parada pendiente' : 'paradas pendientes'}</p></div>
      <dl className="route-planner-facts">
        <div><dt>Propuesta en línea recta</dt><dd>{km(plan.proposedMeters)} km</dd></div>
        <div><dt>Orden inicial</dt><dd>{km(plan.originalMeters)} km</dd></div>
        {saved > 1 ? <div className="is-saving"><dt>Diferencia geográfica</dt><dd>{km(saved)} km</dd></div> : null}
      </dl>
    </div>
    {shown.length ? <LazyRouteMap label={`Ruta sugerida: ${shown.map(s => s.zona.nombre).join(', ')}`} points={points} geometry={road?.coordenadas} fallback={<svg className="route-planner-schematic" viewBox="0 0 400 260" role="img" aria-label={`Orden sugerido: ${shown.map(s => s.zona.nombre).join(', ')}`}>
      <text x="370" y="22">N ↑</text><polyline points={shown.map(s => `${x(s)},${y(s)}`).join(' ')} fill="none" stroke="var(--accent)" strokeWidth="3" strokeDasharray="6 4" />
      {shown.map((s, i) => <g key={s.zona.id}><title>{i + 1}. {s.zona.nombre}</title><circle cx={x(s)} cy={y(s)} r="14" fill={i ? 'var(--accent)' : 'var(--ink)'} /><text x={x(s)} y={y(s) + 5} textAnchor="middle" fill="white">{i + 1}</text></g>)}
    </svg>} /> : <p className="route-planner-note">No hay paradas pendientes con coordenadas para dibujar.</p>}
    {shown.length ? <ol className="route-planner-order">{shown.map((s, i) => <li key={s.zona.id}><span>{i + 1}</span>{s.zona.nombre}<small>{s.pedidos.length} {s.pedidos.length === 1 ? 'pedido' : 'pedidos'}</small></li>)}</ol> : null}
    {shown.length > 1 ? <label className="checkout-field route-planner-start"><span>Empiezo en</span><select value={plan.route[0]?.zona.id ?? ''} disabled={plan.fixedStart} onChange={e => { setStart(e.target.value); onOrder(null); }}>{stops.filter(s => isPending(s) && hasCoordinates(s)).map(s => <option key={s.zona.id} value={s.zona.id}>{s.zona.nombre}</option>)}</select></label> : null}
    {plan.fixedStart ? <small className="route-planner-note">La zona en camino se mantiene primero.</small> : null}
    {plan.missing.length ? <p className="route-planner-warning" role="status">Sin coordenadas: {plan.missing.map(s => s.zona.nombre).join(', ')}. Se mantienen al final de las pendientes, fuera del cálculo.</p> : null}
    {plan.limited ? <p className="route-planner-note">Hay más de 100 puntos; se conserva el orden inicial.</p> : null}
    <div className="route-road-tools"><button className="secondary-button" type="button" disabled={!cycle||shown.length<2||shown.length>25||busy} onClick={()=>void trace()}>{busy?'Trazando…':'Trazar por calles'}</button>
      {road?<p role="status">Recorrido vial: {(road.distancia_m/1000).toFixed(2)} km · {Math.ceil(road.duracion_s/60)} min estimados, sin tráfico en tiempo real. La línea continua sigue las calles del orden elegido.</p>:<p>La línea discontinua une paradas en línea recta. Pulsa «Trazar por calles» para consultar el recorrido vial.</p>}
      {routeError?<p role="alert">{routeError}</p>:null}
    </div>
    <div className="route-planner-actions">{google ? <a className="secondary-button route-planner-google" href={google} target="_blank" rel="noreferrer"><Icon name="map" size={17} />Abrir ruta en Google Maps</a> : null}<button type="button" className="primary-button" disabled={shown.length < 2 || active} onClick={() => onOrder(plan.ids)}>Usar este orden</button>{active ? <button type="button" className="secondary-button" onClick={() => onOrder(null)}>Restaurar orden</button> : null}</div>
    {active ? <p className="route-planner-ok" role="status">Orden sugerido aplicado a la lista. Las entregas se registran con sus botones habituales.</p> : null}
    <p className="route-planner-note">El orden se propone por distancia en línea recta, no por tráfico ni semáforos. El trazado por calles conserva ese orden. Para navegar, usa «Cómo llegar» o Google Maps.</p>
  </section>;
}

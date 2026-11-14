import { useMemo, useState } from 'react';
import { hasCoordinates, isPending, planDelivery, type RouteStop } from '../utils/deliveryRoute';
import './RoutePlanner.css';

export function RoutePlanner({ stops, active, onOrder }: { stops: RouteStop[]; active: boolean; onOrder: (ids: string[] | null) => void }) {
  const [start, setStart] = useState('');
  const plan = useMemo(() => planDelivery(stops, start), [stops, start]);
  const shown = plan.route;
  const lats = shown.map(s => s.zona.lat!), lons = shown.map(s => s.zona.lon!);
  const latSpan = Math.max(0.002, Math.max(...lats) - Math.min(...lats));
  const lonSpan = Math.max(0.002, Math.max(...lons) - Math.min(...lons));
  // Proyección local con escala igual en ambos ejes (distancias pequeñas en Lima).
  const cos = Math.cos((lats[0] ?? -12) * Math.PI / 180);
  const scale = Math.min(320 / (lonSpan * cos), 190 / latSpan);
  const x = (s: RouteStop) => 40 + (s.zona.lon! - Math.min(...lons)) * cos * scale;
  const y = (s: RouteStop) => 35 + (Math.max(...lats) - s.zona.lat!) * scale;
  const km = (n: number) => (n / 1000).toFixed(2);
  return <section className="route-planner" aria-labelledby="route-planner-title">
    <h2 id="route-planner-title">Organiza tus paradas</h2>
    <p>Minimapa esquemático. Compara distancias en línea recta; no representa calles, tráfico ni semáforos.</p>
    {shown.length ? <svg viewBox="0 0 400 260" role="img" aria-label={`Orden sugerido: ${shown.map(s => s.zona.nombre).join(', ')}`}>
      <text x="370" y="22">N ↑</text><polyline points={shown.map(s => `${x(s)},${y(s)}`).join(' ')} fill="none" stroke="#18764f" strokeWidth="3" strokeDasharray="6 4" />
      {shown.map((s, i) => <g key={s.zona.id}><title>{i + 1}. {s.zona.nombre}</title><circle cx={x(s)} cy={y(s)} r="14" fill={i ? '#18764f' : '#172c24'} /><text x={x(s)} y={y(s) + 5} textAnchor="middle" fill="white">{i + 1}</text></g>)}
    </svg> : <p>No hay paradas pendientes con coordenadas para dibujar.</p>}
    <label>Iniciar en<select value={plan.route[0]?.zona.id ?? ''} disabled={plan.fixedStart || shown.length < 2} onChange={e => { setStart(e.target.value); onOrder(null); }}>{stops.filter(s => isPending(s) && hasCoordinates(s)).map(s => <option key={s.zona.id} value={s.zona.id}>{s.zona.nombre}</option>)}</select></label>
    {plan.fixedStart ? <small>La zona en camino se mantiene primero.</small> : null}
    <p>Orden inicial desde ese inicio: <strong>{km(plan.originalMeters)} km</strong>. Propuesta: <strong>{km(plan.proposedMeters)} km</strong>. {plan.orders} pedidos en {stops.filter(isPending).length} paradas pendientes.</p>
    <p>{plan.proposedMeters + 1 < plan.originalMeters ? `Propuesta elegida porque reduce ${km(plan.originalMeters - plan.proposedMeters)} km en línea recta frente al orden inicial.` : 'Se conserva un recorrido de igual o menor distancia en línea recta que el orden inicial.'} Es una aproximación; usa «Cómo llegar» para navegar por calles.</p>
    {plan.missing.length ? <p role="status">Sin coordenadas: {plan.missing.map(s => s.zona.nombre).join(', ')}. Se mantienen al final de las pendientes, fuera del cálculo.</p> : null}
    {plan.limited ? <p>Hay más de 100 puntos; se conserva el orden inicial.</p> : null}
    <ol>{shown.map((s, i) => <li key={s.zona.id}>{i + 1}. {s.zona.nombre} · {s.pedidos.length} pedidos</li>)}</ol>
    <div><button type="button" className="primary-button" disabled={shown.length < 2 || active} onClick={() => onOrder(plan.ids)}>Usar este orden</button><button type="button" className="secondary-button" disabled={!active} onClick={() => onOrder(null)}>Restaurar orden</button></div>
    {active ? <p role="status">Orden sugerido aplicado a la lista. Las entregas se registran con sus botones habituales.</p> : null}
  </section>;
}

export interface RouteStop {
  zona: { id: string; nombre: string; lat?: number | null; lon?: number | null };
  estado: string;
  pedidos: Array<{ id: number; bolsas: number }>;
}
export function isPending(stop: RouteStop) { return stop.estado !== 'entregada' && stop.estado !== 'fallida'; }
export function hasCoordinates(stop: RouteStop): boolean {
  const { lat, lon } = stop.zona;
  return typeof lat === 'number' && typeof lon === 'number' && Number.isFinite(lat) && Number.isFinite(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180;
}
export function distanceMeters(a: RouteStop, b: RouteStop): number {
  const rad = Math.PI / 180;
  const x = Math.sin((b.zona.lat! - a.zona.lat!) * rad / 2) ** 2 + Math.cos(a.zona.lat! * rad) * Math.cos(b.zona.lat! * rad) * Math.sin((b.zona.lon! - a.zona.lon!) * rad / 2) ** 2;
  return 6371000 * 2 * Math.asin(Math.sqrt(Math.min(1, Math.max(0, x))));
}
function length(stops: RouteStop[]) { return stops.slice(1).reduce((total, stop, i) => total + distanceMeters(stops[i], stop), 0); }
export function planDelivery(stops: RouteStop[], startId?: string) {
  const pending = stops.filter(isPending), located = pending.filter(hasCoordinates);
  const inProgress = located.find(s => s.estado === 'en_camino');
  const first = inProgress ?? located.find(s => s.zona.id === startId) ?? located[0];
  const baseline = first ? [first, ...located.filter(s => s !== first)] : [];
  const missing = pending.filter(s => !hasCoordinates(s));
  let route = [...baseline];
  // Límite de trabajo por pantalla; para recorridos grandes se conserva el orden inicial.
  if (first && located.length <= 100) {
    const remaining = located.filter(s => s !== first); route = [first];
    while (remaining.length) {
      let next = 0;
      for (let i = 1; i < remaining.length; i++) if (distanceMeters(route[route.length - 1], remaining[i]) < distanceMeters(route[route.length - 1], remaining[next])) next = i;
      route.push(remaining.splice(next, 1)[0]);
    }
    // No se mueve la primera parada. La ruta es abierta: no añade vuelta al origen.
    for (let pass = 0; pass < 3; pass++) {
      let changed = false;
      for (let i = 1; i < route.length - 1; i++) for (let j = i + 1; j < route.length; j++) {
        const candidate = [...route.slice(0, i), ...route.slice(i, j + 1).reverse(), ...route.slice(j + 1)];
        if (length(candidate) + 0.01 < length(route)) { route = candidate; changed = true; }
      }
      if (!changed) break;
    }
  }
  if (length(route) > length(baseline)) route = baseline;
  return { route, missing, ids: [...route, ...missing, ...stops.filter(s => !isPending(s))].map(s => s.zona.id),
    originalMeters: length(baseline), proposedMeters: length(route), orders: pending.reduce((n, s) => n + s.pedidos.length, 0), fixedStart: Boolean(inProgress), limited: located.length > 100 };
}
export function orderDelivery<T extends RouteStop>(stops: T[], ids: string[] | null): T[] {
  if (!ids) return stops;
  const positions = new Map(ids.map((id, i) => [id, i]));
  return [...stops].sort((a, b) => Number(!isPending(a)) - Number(!isPending(b)) || (positions.get(a.zona.id) ?? ids.length) - (positions.get(b.zona.id) ?? ids.length));
}

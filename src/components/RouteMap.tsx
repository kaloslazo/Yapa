import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export interface RoutePoint { id: string; name: string; lat: number; lon: number; orders: number }

const TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

// mapa real de la ruta sugerida: calles de OpenStreetMap (gratis, ya permitido en la CSP), paradas numeradas y la línea del orden
export function RouteMap({ points, label, geometry }: { points: RoutePoint[]; label: string; geometry?: Array<[number, number]> }) {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const element = host.current;
    if (!element || !points.length) return undefined;
    let map: L.Map | null = null;
    try {
      const m = L.map(element, { scrollWheelZoom: false, zoomControl: false, attributionControl: false });
      map = m;
      L.control.zoom({ position: 'bottomright', zoomInTitle: 'Acercar', zoomOutTitle: 'Alejar' }).addTo(m);
      L.control.attribution({ position: 'bottomleft', prefix: false }).addTo(m);
      L.tileLayer(TILES, { maxZoom: 19, attribution: ATTRIBUTION, className: 'route-map-tiles' }).addTo(m);
      const line = geometry?.length ? geometry.map(([lon,lat])=>L.latLng(lat,lon)) : points.map((p) => L.latLng(p.lat, p.lon));
      L.polyline(line, { color: '#04301d', weight: 7, opacity: 0.15 }).addTo(m);
      L.polyline(line, { color: '#0a7d4e', weight: 4, dashArray: geometry?.length ? undefined : '8 8', className: 'route-map-line' }).addTo(m);
      points.forEach((p, i) => {
        const icon = L.divIcon({ className: '', html: `<span class="route-pin${i ? '' : ' is-first'}">${i + 1}</span>`, iconSize: [30, 30], iconAnchor: [15, 15] });
        L.marker([p.lat, p.lon], { icon, keyboard: false, title: `${i + 1}. ${p.name}` })
          .bindTooltip(`${p.name} · ${p.orders} ${p.orders === 1 ? 'pedido' : 'pedidos'}`, { direction: 'top', offset: [0, -14], className: 'route-map-label' }).addTo(m);
      });
      m.fitBounds(L.latLngBounds(line).pad(0.25), { maxZoom: 16 });
    } catch {
      map?.remove();
      map = null;
    }
    return () => { map?.remove(); };
  }, [points, geometry]);
  return <div className="route-map-real" ref={host} role="img" aria-label={label} />;
}

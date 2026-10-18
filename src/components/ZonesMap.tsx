import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { drawableZones, groupColors, unionLabel } from '../utils/zoneMap';

export interface MapZone {
  id: string;
  name: string;
  group: string;
  lat: number | null;
  lon: number | null;
}

export interface MapUnion {
  a: string;
  b: string;
  distance: number;
  reason: string;
}

interface ZonesMapProps {
  zones: MapZone[];
  unions?: MapUnion[];
  radius: number;
  mergeDistance: number;
  highlightId?: string;
  label: string;
}

const TILES = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';

// mapa real (S-190): círculo de `radius` m por zona (S-191), anillo de `mergeDistance` m en la zona resaltada y líneas entre zonas que podrían unirse
export function ZonesMap({ zones, unions = [], radius, mergeDistance, highlightId, label }: ZonesMapProps) {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const element = host.current;
    const placed = drawableZones(zones);
    if (!element || !placed.length) return undefined;
    const map = L.map(element, { zoomControl: true, scrollWheelZoom: false, attributionControl: true });
    L.tileLayer(TILES, { maxZoom: 19, attribution: ATTRIBUTION }).addTo(map);
    const colors = groupColors(placed.map((z) => z.group));
    const byId = new Map(placed.map((z) => [z.id, z]));
    const bounds = L.latLngBounds([]);

    for (const zone of placed) {
      const color = colors[zone.group];
      const circle = L.circle([zone.lat, zone.lon], { radius, color, weight: zone.id === highlightId ? 4 : 2, fillColor: color, fillOpacity: zone.id === highlightId ? 0.28 : 0.16 }).addTo(map);
      circle.bindTooltip(zone.name, { permanent: true, direction: 'center', className: 'zones-map-label' });
      bounds.extend(circle.getBounds());
      if (zone.id === highlightId) {
        L.circle([zone.lat, zone.lon], { radius: mergeDistance, color: '#52605a', weight: 1.5, dashArray: '6 6', fill: false, interactive: false }).addTo(map);
        bounds.extend(L.latLng(zone.lat, zone.lon).toBounds(mergeDistance * 2));
      }
    }
    for (const union of unions) {
      const a = byId.get(union.a);
      const b = byId.get(union.b);
      if (!a || !b) continue;
      const ok = !union.reason;
      L.polyline([[a.lat, a.lon], [b.lat, b.lon]], { color: ok ? '#2f7d5b' : '#6b7771', weight: ok ? 4 : 3, dashArray: ok ? undefined : '4 8' })
        .bindTooltip(unionLabel(union.distance, union.reason), { sticky: true }).addTo(map);
    }
    map.fitBounds(bounds, { padding: [24, 24], maxZoom: 17 });
    return () => { map.remove(); };
  }, [zones, unions, radius, mergeDistance, highlightId]);

  if (!drawableZones(zones).length) return <p className="admin-muted">Todavía no hay zonas con ubicación para mostrar en el mapa.</p>;
  return <div className="zones-map" ref={host} role="region" aria-label={label} tabIndex={0} />;
}

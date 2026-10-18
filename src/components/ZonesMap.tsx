import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { drawableZones, focusZoneIds, groupColors, unionLabel } from '../utils/zoneMap';

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
const PADDING: L.PointExpression = [24, 24];

// mapa real (S-190): círculo de `radius` m por zona (S-191), anillo de `mergeDistance` m en la zona resaltada
// y líneas entre zonas que podrían unirse. Encuadra primero las zonas que se pueden unir; "Ver todas" las muestra todas.
export function ZonesMap({ zones, unions = [], radius, mergeDistance, highlightId, label }: ZonesMapProps) {
  const host = useRef<HTMLDivElement>(null);
  const showAll = useRef<() => void>(() => undefined);

  useEffect(() => {
    const element = host.current;
    const placed = drawableZones(zones);
    if (!element || !placed.length) return undefined;
    let map: L.Map | null = null;
    try {
      map = L.map(element, { scrollWheelZoom: false });
      L.tileLayer(TILES, { maxZoom: 19, attribution: ATTRIBUTION }).addTo(map);
      const colors = groupColors(placed.map((z) => z.group));
      const byId = new Map(placed.map((z) => [z.id, z]));
      const focusIds = highlightId ? new Set([highlightId]) : focusZoneIds(placed, unions);
      const everything = L.latLngBounds([]);
      const focus = L.latLngBounds([]);

      for (const zone of placed) {
        const center = L.latLng(zone.lat, zone.lon);
        const color = colors[zone.group];
        const highlighted = zone.id === highlightId;
        L.circle(center, { radius, color, weight: highlighted ? 4 : 2, fillColor: color, fillOpacity: highlighted ? 0.28 : 0.16 })
          .bindTooltip(zone.name, { permanent: true, direction: 'center', className: 'zones-map-label' }).addTo(map);
        const area = center.toBounds(radius * 2);
        everything.extend(area);
        if (focusIds.has(zone.id)) focus.extend(area);
        if (highlighted) {
          L.circle(center, { radius: mergeDistance, color: '#52605a', weight: 1.5, dashArray: '6 6', fill: false, interactive: false }).addTo(map);
          focus.extend(center.toBounds(mergeDistance * 2));
          everything.extend(center.toBounds(mergeDistance * 2));
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
      const view = map;
      view.fitBounds(focus.isValid() ? focus : everything, { padding: PADDING, maxZoom: 17 });
      showAll.current = () => view.fitBounds(everything, { padding: PADDING, maxZoom: 17 });
    } catch {
      // un fallo del mapa no debe tumbar la pantalla: la lista de zonas sigue visible (MP-04, MP-05)
    }
    return () => { map?.remove(); };
  }, [zones, unions, radius, mergeDistance, highlightId]);

  if (!drawableZones(zones).length) return <p className="admin-muted">Todavía no hay zonas con ubicación para mostrar en el mapa.</p>;
  return (
    <div className="zones-map-wrap">
      <div className="zones-map" ref={host} role="region" aria-label={label} tabIndex={0} />
      {drawableZones(zones).length > 1 ? <button className="text-button" type="button" onClick={() => showAll.current()}>Ver todas las zonas</button> : null}
    </div>
  );
}

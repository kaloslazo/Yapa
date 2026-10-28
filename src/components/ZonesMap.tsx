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

export interface ZonesMapProps {
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
      map = L.map(element, { scrollWheelZoom: false, zoomControl: false, attributionControl: false });
      L.control.zoom({ position: 'bottomright', zoomInTitle: 'Acercar', zoomOutTitle: 'Alejar' }).addTo(map);
      L.control.attribution({ position: 'bottomleft', prefix: false }).addTo(map);
      // el mapa base va en tonos apagados (CSS) para que resalten los colores de las zonas
      L.tileLayer(TILES, { maxZoom: 19, attribution: ATTRIBUTION, className: 'zones-map-tiles' }).addTo(map);
      const colors = groupColors(placed.map((z) => z.group));
      const byId = new Map(placed.map((z) => [z.id, z]));
      const focusIds = highlightId ? new Set([highlightId]) : focusZoneIds(placed, unions);
      const everything = L.latLngBounds([]);
      const focus = L.latLngBounds([]);

      for (const zone of placed) {
        const center = L.latLng(zone.lat, zone.lon);
        const color = colors[zone.group];
        const highlighted = zone.id === highlightId;
        L.circle(center, { radius, color, weight: highlighted ? 3 : 2, opacity: 0.9, fillColor: color, fillOpacity: highlighted ? 0.24 : 0.14 }).addTo(map);
        // el punto marca la portería; la etiqueta va arriba para no tapar el círculo
        L.circleMarker(center, { radius: 7, color: '#fffdf9', weight: 3, fillColor: color, fillOpacity: 1 })
          .bindTooltip(zone.name, { permanent: true, direction: 'top', offset: [0, -10], className: 'zones-map-label' }).addTo(map);
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
      {drawableZones(zones).length > 1 ? <button className="zones-map-all" type="button" onClick={() => showAll.current()}>Ver todas las zonas</button> : null}
    </div>
  );
}

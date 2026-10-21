import { lazy, Suspense } from 'react';
import type { ZonesMapProps } from './ZonesMap';

// FE-SG-2: Leaflet solo se baja cuando alguien abre un mapa
const ZonesMap = lazy(() => import('./ZonesMap').then((module) => ({ default: module.ZonesMap })));

export function LazyZonesMap(props: ZonesMapProps) {
  return <Suspense fallback={<div className="zones-map-wrap"><div className="zones-map" aria-busy="true" aria-label={props.label} /></div>}><ZonesMap {...props} /></Suspense>;
}

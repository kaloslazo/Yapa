import { lazy, Suspense, type ReactNode } from 'react';
import type { RoutePoint } from './RouteMap';

// como LazyZonesMap: Leaflet solo se baja cuando hay una ruta que mostrar; mientras, el esquema
const RouteMap = lazy(() => import('./RouteMap').then((module) => ({ default: module.RouteMap })));

export function LazyRouteMap({ points, label, fallback, geometry }: { points: RoutePoint[]; label: string; fallback: ReactNode; geometry?: Array<[number, number]> }) {
  return <Suspense fallback={fallback}><RouteMap points={points} label={label} geometry={geometry} /></Suspense>;
}

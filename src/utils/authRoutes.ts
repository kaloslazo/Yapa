// el acceso vive en páginas propias: /entrar para vecinos y /equipo para el personal (antes era un modal)

export type AuthPageId = 'entrar' | 'equipo';
export type StaffLoginKind = 'admin' | 'compras' | 'armador' | 'atencion' | 'porteria' | 'transportista' | 'proveedor';
export type ReturnView = 'cart' | 'orders' | 'zone' | 'cuenta';

export const STAFF_LOGIN_KINDS: StaffLoginKind[] = ['admin', 'compras', 'armador', 'atencion', 'porteria', 'transportista', 'proveedor'];
const RETURN_VIEWS: ReturnView[] = ['cart', 'orders', 'zone', 'cuenta'];

export interface AuthRoute { page: AuthPageId | null; rol?: StaffLoginKind; volver?: ReturnView }

// solo se vuelve a una vista de la tienda: un link armado no puede mandar a otro sitio
export const safeReturn = (value: string | null | undefined): ReturnView | null =>
  RETURN_VIEWS.includes(value as ReturnView) ? (value as ReturnView) : null;

export function authRouteFromLocation(pathname: string, search: string): AuthRoute {
  const path = pathname.replace(/\/$/, '');
  const page = path === '/entrar' ? 'entrar' : path === '/equipo' ? 'equipo' : null;
  if (!page) return { page: null };
  const params = new URLSearchParams(search);
  const route: AuthRoute = { page };
  const rol = params.get('rol') as StaffLoginKind | null;
  if (page === 'equipo' && rol && STAFF_LOGIN_KINDS.includes(rol)) route.rol = rol;
  const volver = safeReturn(params.get('volver'));
  if (volver) route.volver = volver;
  return route;
}

export function authHref(page: AuthPageId, options: { rol?: StaffLoginKind; volver?: ReturnView } = {}): string {
  const params = new URLSearchParams();
  if (options.rol) params.set('rol', options.rol);
  if (options.volver) params.set('volver', options.volver);
  const query = params.toString();
  return `/${page}${query ? `?${query}` : ''}`;
}

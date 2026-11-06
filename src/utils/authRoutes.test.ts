import { describe, expect, it } from 'vitest';
import { authHref, authRouteFromLocation, safeReturn } from './authRoutes';

// el acceso vive en páginas propias: /entrar para vecinos y /equipo para el personal
describe('rutas del acceso', () => {
  it('reconoce /entrar y /equipo, con o sin barra final', () => {
    expect(authRouteFromLocation('/entrar', '')).toEqual({ page: 'entrar' });
    expect(authRouteFromLocation('/equipo/', '')).toEqual({ page: 'equipo' });
    expect(authRouteFromLocation('/', '')).toEqual({ page: null });
    expect(authRouteFromLocation('/unete/abc', '')).toEqual({ page: null });
  });

  it('el link del equipo llega con el rol elegido; un rol que no existe se ignora', () => {
    expect(authRouteFromLocation('/equipo', '?rol=porteria')).toEqual({ page: 'equipo', rol: 'porteria' });
    expect(authRouteFromLocation('/equipo', '?rol=hacker')).toEqual({ page: 'equipo' });
    expect(authRouteFromLocation('/entrar', '?rol=porteria')).toEqual({ page: 'entrar' });
  });

  it('después de entrar solo se vuelve a una vista de la tienda', () => {
    expect(authRouteFromLocation('/entrar', '?volver=cart')).toEqual({ page: 'entrar', volver: 'cart' });
    expect(authRouteFromLocation('/entrar', '?volver=https://malo.com')).toEqual({ page: 'entrar' });
    expect(safeReturn('orders')).toBe('orders');
    expect(safeReturn('https://malo.com')).toBeNull();
    expect(safeReturn('//malo.com')).toBeNull();
    expect(safeReturn(null)).toBeNull();
  });

  it('arma los links', () => {
    expect(authHref('entrar')).toBe('/entrar');
    expect(authHref('entrar', { volver: 'cart' })).toBe('/entrar?volver=cart');
    expect(authHref('equipo', { rol: 'porteria' })).toBe('/equipo?rol=porteria');
  });
});

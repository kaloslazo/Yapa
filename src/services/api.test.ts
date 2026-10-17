import { describe, expect, it } from 'vitest';
import { ApiError, createApi } from './api';
import { toProduct } from './mappers';

describe('FE-A · producto desde la API', () => {
  it('muestra precio, avance, siguiente tramo y ahorro frente al supermercado', () => {
    const product = toProduct({
      id: 'PAPA-AMARILLA', nombre: 'Papa amarilla', categoria: 'FRESCOS', unidad: 'kg', paso: '1', maximo_por_pedido: '10',
      precio_max: '4.03', pedido_total: '27', siguiente_tramo: { desde: '100', precio: '3.79' },
      tramos: [{ desde: '0', precio: '4.03' }, { desde: '100', precio: '3.79' }],
      referencias: [{ tipo: 'SUPERMERCADO', fuente: 'Plaza Vea', precio: '7.99', visto: '2026-09-24' }],
    });
    expect(product.price).toBe(4.03);
    expect(product.ordered).toBe(27);
    expect(product.nextTier).toEqual({ from: 100, price: 3.79 });
    expect(product.supermarket?.price).toBe(7.99);
    expect(product.supermarketSaving).toBeCloseTo(49.56, 1);
    expect(product.image).toBe('/images/products/papa-amarilla.png');
  });
});

describe('FE-C · cliente de la API', () => {
  it('manda el token CSRF y la cookie en un POST', async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    const api = createApi(async (url, init) => {
      calls.push({ url: String(url), init: init ?? {} });
      return new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    });
    api.setCsrf('token-123');
    await api.post('/api/pedidos', { lineas: {} });
    expect(calls[0].url).toBe('/api/pedidos');
    expect(calls[0].init.credentials).toBe('include');
    expect(new Headers(calls[0].init.headers).get('X-Yapa-CSRF')).toBe('token-123');
  });

  it('convierte un 422 en un error con el código y el mensaje', async () => {
    const api = createApi(async () => new Response(JSON.stringify({ error: { codigo: 'SUBTOTAL_BELOW_MINIMUM', mensaje: 'Faltan S/ 3.20.' } }), { status: 422 }));
    await expect(api.post('/api/cotizar', {})).rejects.toMatchObject({ code: 'SUBTOTAL_BELOW_MINIMUM', message: 'Faltan S/ 3.20.', status: 422 });
    await expect(api.post('/api/cotizar', {})).rejects.toBeInstanceOf(ApiError);
  });
});

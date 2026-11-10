// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { describe, expect, it, vi } from 'vitest';
import { Catalog } from './Catalog';
import { ProductSheet } from './Sheet';
import { PrivacyPage } from './PrivacyPage';
import { toProduct } from '../services/mappers';
import { photoCredits } from '../data/photoCredits';

// tienda simple (11/2026): la grilla muestra foto, precio, nombre y un «+»; el detalle va en la ficha
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

const raw = (id: string, categoria: string, precio: string, tramos: Array<[string, string]>, pedido: string, supermercado?: string) => ({
  id, nombre: id === 'CEBOLLA-ROJA' ? 'Cebolla roja' : 'Lejía galón', categoria, unidad: categoria === 'FRESCOS' ? 'kg' : 'unidad', paso: '1', maximo_por_pedido: '10',
  precio_max: precio, pedido_total: pedido, tramos: tramos.map(([desde, p]) => ({ desde, precio: p })),
  siguiente_tramo: tramos.map(([desde, p]) => ({ desde, precio: p })).find((t) => Number(t.desde) > Number(pedido)) ?? null,
  referencias: supermercado ? [{ tipo: 'SUPERMERCADO', fuente: 'Plaza Vea', precio: supermercado, visto: '2026-09-24' }] : [],
});
const cebolla = toProduct(raw('CEBOLLA-ROJA', 'FRESCOS', '2.35', [['0', '2.35'], ['80', '2.02']], '32', '3.89'));
const lejia = toProduct(raw('LEJIA-GALON', 'LIMPIEZA', '7.09', [['0', '7.09'], ['12', '6.32']], '0'));

async function render(element: ReturnType<typeof createElement>) {
  const host = document.createElement('div');
  document.body.appendChild(host);
  await act(async () => { createRoot(host).render(element); });
  return host;
}

describe('grilla de la tienda', () => {
  it('cada producto se ve con su foto o su galón, el precio, el nombre y un botón para agregar', async () => {
    const onAdd = vi.fn();
    const host = await render(createElement(Catalog, { products: [cebolla, lejia], categories: ['Frescos', 'Limpieza'], cart: {}, category: 'Todos', query: '', onCategoryChange: vi.fn(), onAdd, onDecrease: vi.fn(), onOpen: vi.fn(), onClearFilters: vi.fn() }));
    expect(host.querySelector('img[alt="Cebolla roja"]')?.getAttribute('src')).toBe('/images/products/cebolla-roja.webp');
    expect(host.querySelector('.product-jug')).not.toBeNull();
    expect(host.textContent).toContain('S/ 2.35');
    expect(host.textContent).toContain('−40%');
    expect(host.textContent).toContain('En el súper');
    await act(async () => { (host.querySelector('[aria-label="Agregar Cebolla roja"]') as HTMLButtonElement).click(); });
    expect(onAdd).toHaveBeenCalledWith(cebolla);
  });

  it('la grilla no muestra tramos: eso queda para la ficha', async () => {
    const host = await render(createElement(Catalog, { products: [cebolla], categories: ['Frescos'], cart: { 'CEBOLLA-ROJA': 2 }, category: 'Todos', query: '', onCategoryChange: vi.fn(), onAdd: vi.fn(), onDecrease: vi.fn(), onOpen: vi.fn(), onClearFilters: vi.fn() }));
    expect(host.textContent).not.toContain('baja a');
    expect(host.textContent).toContain('2 kg');
  });
});

describe('ficha del producto', () => {
  it('dice cuánto ahorras y cuánto falta entre todos para que baje', async () => {
    const host = await render(createElement(ProductSheet, { product: cebolla, quantity: 0, onAdd: vi.fn(), onDecrease: vi.fn(), onClose: vi.fn() }));
    const text = document.body.textContent ?? '';
    expect(text).toContain('Ahorras S/ 1.54 por kg frente a Plaza Vea');
    expect(text).toContain('Si entre todos llegamos a 80 kg, baja a S/ 2.02');
    expect(text).toContain('Agregar · S/ 2.35');
    host.remove();
  });
});

describe('créditos de las fotos (licencias CC)', () => {
  it('cada foto de Commons nombra autor y licencia en la página de privacidad', async () => {
    const host = await render(createElement(PrivacyPage));
    expect(host.textContent).toContain('Fotos de los productos');
    for (const credit of photoCredits) expect(host.textContent, credit.product).toContain(`foto de ${credit.author}`);
  });
});

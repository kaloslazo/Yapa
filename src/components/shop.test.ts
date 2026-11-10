// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { describe, expect, it, vi } from 'vitest';
import { ProductGrid } from './Catalog';
import { HomePage } from './HomePage';
import { ProductPage } from './ProductPage';
import { PrivacyPage } from './PrivacyPage';
import { toProduct } from '../services/mappers';
import { photoCredits } from '../data/photoCredits';

// estructura nueva de la tienda (fase 1): inicio por secciones, tarjeta con foto y ficha del producto como pantalla
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

const raw = (id: string, nombre: string, categoria: string, precio: string, tramos: Array<[string, string]>, pedido: string, supermercado?: string) => ({
  id, nombre, categoria, unidad: categoria === 'FRESCOS' ? 'kg' : 'unidad', paso: '1', maximo_por_pedido: '10',
  precio_max: precio, pedido_total: pedido, tramos: tramos.map(([desde, p]) => ({ desde, precio: p })),
  siguiente_tramo: tramos.map(([desde, p]) => ({ desde, precio: p })).find((t) => Number(t.desde) > Number(pedido)) ?? null,
  referencias: supermercado ? [{ tipo: 'SUPERMERCADO', fuente: 'Plaza Vea', precio: supermercado, visto: '2026-09-24' }] : [],
});
const cebolla = toProduct(raw('CEBOLLA-ROJA', 'Cebolla roja', 'FRESCOS', '2.35', [['0', '2.35'], ['80', '2.02']], '32', '3.89'));
const papa = toProduct(raw('PAPA-AMARILLA', 'Papa amarilla', 'FRESCOS', '4.03', [['0', '4.03'], ['100', '3.79']], '33', '7.99'));
const lejia = toProduct(raw('LEJIA-GALON', 'Lejía galón', 'LIMPIEZA', '7.09', [['0', '7.09'], ['12', '6.32']], '0'));
const actions = { onAdd: vi.fn(), onDecrease: vi.fn(), onOpen: vi.fn() };

async function render(element: ReturnType<typeof createElement>) {
  const host = document.createElement('div');
  document.body.appendChild(host);
  await act(async () => { createRoot(host).render(element); });
  return host;
}

describe('tarjeta de producto', () => {
  it('foto o galón, precio, nombre, ahorro y un botón para agregar', async () => {
    const onAdd = vi.fn();
    const host = await render(createElement(ProductGrid, { products: [cebolla, lejia], cart: {}, ...actions, onAdd }));
    expect(host.querySelector('img[alt="Cebolla roja"]')?.getAttribute('src')).toBe('/images/products/cebolla-roja.webp');
    expect(host.querySelector('.product-jug')).not.toBeNull();
    expect(host.textContent).toContain('S/ 2.35');
    expect(host.textContent).toContain('−40%');
    await act(async () => { (host.querySelector('[aria-label="Agregar Cebolla roja"]') as HTMLButtonElement).click(); });
    expect(onAdd).toHaveBeenCalledWith(cebolla);
  });
  it('con cantidad, el «+» se vuelve el contador', async () => {
    const host = await render(createElement(ProductGrid, { products: [cebolla], cart: { 'CEBOLLA-ROJA': 2 }, ...actions }));
    expect(host.querySelector('[aria-label="Cantidad de Cebolla roja"]')?.textContent).toContain('2 kg');
  });
});

describe('inicio por secciones', () => {
  const props = { products: [papa, cebolla, lejia], results: [], query: '', cart: {}, cycleOpen: true, countdown: 'Cierra en 1 d 11 h', delivery: 'sáb 14 nov', signedIn: false, balance: 0, ...actions, onGroup: vi.fn(), onExplore: vi.fn(), onHow: vi.fn(), onLogin: vi.fn(), onBalance: vi.fn(), onClearSearch: vi.fn() };
  it('la semana arriba y luego categorías, mejores precios, por bajar y todo', async () => {
    const host = await render(createElement(HomePage, props));
    const text = host.textContent ?? '';
    for (const part of ['Cierra en 1 d 11 h', 'Sáb 14 nov', 'Categorías', 'Tubérculos', 'Mejores precios', 'Están por bajar', 'Todo lo de esta semana']) expect(text, part).toContain(part);
    expect(text).toContain('Faltan 48 kg para que baje a S/ 2.02');
  });
  it('con una búsqueda solo muestra los resultados', async () => {
    const host = await render(createElement(HomePage, { ...props, query: 'cebo', results: [cebolla] }));
    expect(host.textContent).toContain('Resultados para «cebo»');
    expect(host.textContent).not.toContain('Mejores precios');
  });
});

describe('ficha del producto', () => {
  it('precio, ahorro, cómo baja el precio y un solo botón para agregar', async () => {
    const host = await render(createElement(ProductPage, { product: cebolla, quantity: 0, delivery: 'sáb 14 nov', onAdd: vi.fn(), onDecrease: vi.fn(), onBack: vi.fn(), onCart: vi.fn(), onShare: vi.fn() }));
    const text = host.textContent ?? '';
    expect(text).toContain('Ahorras S/ 1.54');
    expect(text).toContain('Desde 80 kg entre todos');
    expect(text).toContain('faltan 48 kg para el siguiente precio');
    expect(text).toContain('Agregar a la canasta · S/ 2.35');
  });
});

describe('créditos de las fotos (licencias CC)', () => {
  it('cada foto de Commons nombra autor y licencia en la página de privacidad', async () => {
    const host = await render(createElement(PrivacyPage));
    expect(host.textContent).toContain('Fotos de los productos');
    for (const credit of photoCredits) expect(host.textContent, credit.product).toContain(`foto de ${credit.author}`);
  });
});

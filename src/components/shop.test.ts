// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { describe, expect, it, vi } from 'vitest';
import { ProductGrid } from './Catalog';
import { HomePage } from './HomePage';
import { ProductPage } from './ProductPage';
import { PrivacyPage } from './PrivacyPage';
import { CartPage } from './CartPage';
import { PayPage } from './PayPage';
import type { Order, Quote } from '../types';
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
  it('la cuenta regresiva en fichas y la oferta más fuerte al lado con su botón', async () => {
    const onAdd = vi.fn();
    const host = await render(createElement(HomePage, { ...props, onAdd, countdownParts: [{ value: 1, unit: 'día' }, { value: 11, unit: 'h' }, { value: 5, unit: 'min' }] }));
    expect([...host.querySelectorAll('.countdown-cell small')].map((cell) => cell.textContent)).toEqual(['día', 'h', 'min']);
    expect(host.querySelector('.countdown-cell .sr-only')?.textContent).toBe('01');
    const spotlight = host.querySelector('.spotlight');
    expect(spotlight?.textContent).toContain('Papa amarilla'); // la que más ahorra frente al súper
    expect(spotlight?.textContent).toContain('−50% frente al súper');
    await act(async () => { (spotlight?.querySelector('.spotlight-add') as HTMLButtonElement).click(); });
    expect(onAdd).toHaveBeenCalledWith(papa);
  });
  it('cada sección tiene su ícono y las categorías dicen cuántos productos hay', async () => {
    const host = await render(createElement(HomePage, props));
    expect(host.querySelectorAll('.sec-head .sec-icon')).toHaveLength(4);
    expect(host.querySelector('.cat-tile')?.textContent).toBe('Tubérculos1 producto');
  });
  it('con una búsqueda solo muestra los resultados', async () => {
    const host = await render(createElement(HomePage, { ...props, query: 'cebo', results: [cebolla] }));
    expect(host.textContent).toContain('Resultados para «cebo»');
    expect(host.textContent).not.toContain('Mejores precios');
  });
  // iteración 62: el avance del grupo en la tarjeta de la semana (AG-G, S-321)
  const meterWidth = (host: HTMLElement) => host.querySelector<HTMLElement>('.week-card .meter span')?.style.width;
  it('con sesión y zona dice cuántos pedidos lleva el edificio y llena la barra', async () => {
    const host = await render(createElement(HomePage, { ...props, signedIn: true, group: { verified: 5, minimum: 8 } }));
    expect(host.querySelector('.week-card')?.textContent).toContain('Tu edificio lleva 5 de 8 pedidos para comprar juntos');
    expect(meterWidth(host)).toBe('62.5%');
  });
  it('con 8 o más dice que el edificio ya llegó y la barra queda llena', async () => {
    const host = await render(createElement(HomePage, { ...props, signedIn: true, group: { verified: 9, minimum: 8 } }));
    expect(host.querySelector('.week-card')?.textContent).toContain('Tu edificio ya llegó a los 8 pedidos para comprar juntos');
    expect(meterWidth(host)).toBe('100%');
  });
  it('sin avance o con el ciclo cerrado la tarjeta queda como está', async () => {
    for (const extra of [{ group: null }, { signedIn: true, group: { verified: 5, minimum: 8 }, cycleOpen: false }]) {
      const host = await render(createElement(HomePage, { ...props, ...extra }));
      expect(host.querySelector('.week-card')?.textContent).not.toContain('Tu edificio');
      expect(meterWidth(host)).toBeUndefined();
    }
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

// fase 2: la canasta dice cuánto falta para el mínimo y el pago es una pantalla con Yape, Plin y saldo
describe('canasta', () => {
  const base = { savings: 0, onAdd: vi.fn(), onDecrease: vi.fn(), onOpen: vi.fn(), onClear: vi.fn(), onBack: vi.fn() };
  it('debajo del mínimo dice cuánto falta y no deja pagar', async () => {
    const host = await render(createElement(CartPage, { ...base, lines: [{ product: cebolla, quantity: 2 }], subtotal: 4.7, onCheckout: vi.fn() }));
    expect(host.textContent).toContain('Te faltan S/ 45.30 para el mínimo de S/ 50.00');
    expect((host.querySelector('.sticky-cta button') as HTMLButtonElement).disabled).toBe(true);
  });
  it('con el mínimo deja ir a pagar con el total máximo', async () => {
    const onCheckout = vi.fn();
    const host = await render(createElement(CartPage, { ...base, lines: [{ product: papa, quantity: 13 }], subtotal: 52.39, onCheckout }));
    const button = host.querySelector('.sticky-cta button') as HTMLButtonElement;
    expect(button.textContent).toBe('Ir a pagar · S/ 57.39');
    await act(async () => { button.click(); });
    expect(onCheckout).toHaveBeenCalled();
  });
  it('vacía avisa qué hacer', async () => {
    const host = await render(createElement(CartPage, { ...base, lines: [], subtotal: 0, onCheckout: vi.fn() }));
    expect(host.textContent).toContain('Tu canasta está vacía');
  });
});

describe('pago', () => {
  const quote: Quote = { lines: [{ id: 'PAPA-AMARILLA', name: 'Papa amarilla', quantity: 13, maxPrice: 4.03, total: 52.39 }], subtotal: 52.39, delivery: 5, total: 57.39, supermarketSaving: 51.48, balance: 2 };
  const base = { zone: undefined, delivery: 'sáb 14 nov', cycleOpen: true, onBack: vi.fn(), onOpenOrders: vi.fn(), onKeepShopping: vi.fn() };
  it('Yape por defecto, usa el saldo y se puede cambiar a Plin sin saldo', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    const host = await render(createElement(PayPage, { ...base, quote, confirmation: null, onSubmit }));
    expect(host.textContent).toContain('Confirmar pedido · S/ 55.39');
    await act(async () => { (host.querySelector('input[value="PLIN"]') as HTMLInputElement).click(); });
    await act(async () => { (host.querySelector('input[type="checkbox"]') as HTMLInputElement).click(); });
    expect(host.textContent).toContain('Confirmar pedido · S/ 57.39');
    await act(async () => { (host.querySelector('form') as HTMLFormElement).requestSubmit(); });
    expect(onSubmit).toHaveBeenCalledWith('PLIN', false);
  });
  it('confirmado muestra cuánto yapear y el código', async () => {
    const order = { id: 1043, method: 'YAPE', paymentCode: 'YP-1043', toPay: 55.39 } as Order;
    const host = await render(createElement(PayPage, { ...base, quote: null, confirmation: order, onSubmit: vi.fn() }));
    expect(host.textContent).toContain('Pedido 1043 registrado');
    expect(host.textContent).toContain('S/ 55.39');
    expect(host.querySelector('.pay-code')?.textContent).toContain('YP-1043');
  });
});

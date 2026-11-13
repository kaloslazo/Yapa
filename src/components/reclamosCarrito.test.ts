// @vitest-environment jsdom
// Iteración 65 · pedidos y reclamos del vecino como un carrito (RV-C..RV-E). Spec: api/docs/desarrollo/65-reclamos-como-un-carrito.md
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { OrdersPage } from './OrdersPage';
import { toOrder } from '../services/mappers';

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any
let root: Root;
let host: HTMLDivElement;
afterEach(async () => { if (root) await act(async () => root.unmount()); host?.remove(); });
async function mount(element: React.ReactNode) {
  host = document.createElement('div'); document.body.append(host); root = createRoot(host);
  await act(async () => { root.render(element); });
}
const line = (id: string, nombre: string, cantidad: string) => ({ id, nombre, cantidad, precio_max: '2.00', total: '10.00' });
const order = toOrder({ id: 12, ciclo: '2026-W40', zona: 'Z-LINCE-01', cliente: 105, estado: 'LIQUIDADO', pago: 'VERIFICADO', metodo: 'YAPE', total: '72.76', lineas: [line('PAPA-AMARILLA', 'Papa amarilla', '8'), line('CEBOLLA-ROJA', 'Cebolla roja', '5')] });
const data = { orders: [order], balance: 0, returned: 0, supermarketSaving: 0, refunds: [] };
const claimables = [
  { order: 12, product: 'PAPA-AMARILLA', name: 'Papa amarilla', quantity: 8, until: '2026-10-04T10:30:00-05:00' },
  { order: 12, product: 'CEBOLLA-ROJA', name: 'Cebolla roja', quantity: 5, until: '2026-10-04T10:30:00-05:00' },
];
const page = (onClaim = vi.fn().mockResolvedValue(undefined), claims: unknown[] = []) => createElement(OrdersPage, { data, claimables, claims: claims as never, onBack: vi.fn(), onCancel: vi.fn(), onWithdraw: vi.fn(), onClaim });

describe('RV-C · el pedido como un carrito', () => {
  it('cada línea muestra la foto, el nombre y la cantidad', async () => {
    await mount(page());
    const lines = host.querySelectorAll('.order-cart li');
    expect(lines).toHaveLength(2);
    expect(lines[0].querySelector('.product-thumb')).not.toBeNull();
    expect(lines[0].textContent).toContain('Papa amarilla');
    expect(lines[0].textContent).toContain('8');
  });
});

describe('RV-D · reclamar tocando el producto', () => {
  it('no hay desplegable; la tarjeta elegida va en el reclamo', async () => {
    const onClaim = vi.fn().mockResolvedValue(undefined);
    await mount(page(onClaim));
    const form = host.querySelector('.claim-form')!;
    expect(form.querySelector('select')).toBeNull();
    const cards = form.querySelectorAll<HTMLInputElement>('.claim-pick input[type=radio]');
    expect(cards).toHaveLength(2);
    await act(async () => { cards[1].click(); });
    const photo = form.querySelector<HTMLInputElement>('input[type=file]')!;
    Object.defineProperty(photo, 'files', { value: [new File(['x'], 'f.png', { type: 'image/png' })] });
    photo.required = false; // jsdom no valida archivos: la foto se comprueba en el motor (RC-04)
    await act(async () => { (form as HTMLFormElement).requestSubmit(); });
    const sent = onClaim.mock.calls[0][0] as FormData;
    expect(sent.get('pedido')).toBe('12');
    expect(sent.get('producto')).toBe('CEBOLLA-ROJA');
  });
});

describe('RV-E · tus reclamos', () => {
  it('se ven con el producto, el motivo, el estado y lo devuelto', async () => {
    await mount(page(undefined, [{ id: 1, order: 12, product: 'CEBOLLA-ROJA', name: 'Cebolla roja', quantity: 1, reason: 'DANADO', status: 'APROBADO', returned: 2.1 }]));
    const item = host.querySelector('.claim-history li')!;
    expect(item.querySelector('.product-thumb')).not.toBeNull();
    expect(item.textContent).toContain('Cebolla roja');
    expect(item.textContent).toContain('Llegó dañado');
    expect(item.textContent).toContain('Aprobado');
    expect(item.textContent).toContain('2.10');
  });
});

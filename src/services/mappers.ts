// convierte las respuestas de la API (montos como texto, S-154) a los tipos de la tienda
import { categoryNames, lookFor } from '../data/presentation';
import type { Account, CycleState, Order, OrderLine, Product, Quote, ReferencePrice, Settlement, Zone } from '../types';

const num = (value: unknown) => Number(value ?? 0);

/* eslint-disable @typescript-eslint/no-explicit-any */
type Raw = Record<string, any>;

export function toProduct(raw: Raw): Product {
  const look = lookFor(raw.id, raw.categoria);
  const references: ReferencePrice[] = (raw.referencias ?? []).map((r: Raw) => ({ kind: r.tipo, source: r.fuente, price: num(r.precio), seen: r.visto }));
  const supermarket = references.find((r) => r.kind === 'SUPERMERCADO') ?? null;
  const price = num(raw.precio_max);
  return {
    id: raw.id,
    name: raw.nombre,
    category: categoryNames[raw.categoria] ?? raw.categoria,
    price,
    unit: raw.unidad,
    step: num(raw.paso),
    maxPerOrder: num(raw.maximo_por_pedido),
    ordered: num(raw.pedido_total),
    nextTier: raw.siguiente_tramo ? { from: num(raw.siguiente_tramo.desde), price: num(raw.siguiente_tramo.precio) } : null,
    tiers: (raw.tramos ?? []).map((t: Raw) => ({ from: num(t.desde), price: num(t.precio) })),
    references,
    supermarket,
    supermarketSaving: supermarket && supermarket.price > price ? (1 - price / supermarket.price) * 100 : null,
    detail: look.detail,
    art: look.art,
    image: look.image ?? null,
    emoji: look.emoji,
  };
}

export function toLine(raw: Raw): OrderLine {
  return { id: raw.id, name: raw.nombre, quantity: num(raw.cantidad), maxPrice: num(raw.precio_max), total: num(raw.total) };
}

function toSettlement(raw: Raw | undefined): Settlement | null {
  if (!raw) return null;
  const comparison: Settlement['comparison'] = {};
  for (const [kind, value] of Object.entries(raw.comparacion ?? {}) as Array<[string, Raw]>) {
    comparison[kind as 'MERCADO' | 'SUPERMERCADO'] = { before: num(value.costaba), saving: num(value.ahorro) };
  }
  return { status: raw.estado, paid: num(raw.pagado), cost: num(raw.costo), returned: num(raw.devuelto), destination: raw.destino ?? null, benefit: num(raw.beneficio), comparison };
}

export function toOrder(raw: Raw): Order {
  return {
    id: raw.id, cycle: raw.ciclo, zoneId: raw.zona, customer: raw.cliente, customerName: raw.vecino,
    status: raw.estado, payment: raw.pago, method: raw.metodo, paymentCode: raw.codigo_pago,
    total: num(raw.total), subtotal: num(raw.subtotal), delivery: num(raw.envio), withBalance: num(raw.con_saldo),
    toPay: num(raw.a_yapear), delivered: Boolean(raw.entregado), cancellable: Boolean(raw.cancelable),
    lines: (raw.lineas ?? []).map(toLine), settlement: toSettlement(raw.liquidacion),
    bags: raw.bolsas?.map((b: Raw) => ({ number: b.numero, photo: b.foto })),
  };
}

export function toQuote(raw: Raw): Quote {
  return { lines: raw.lineas.map(toLine), subtotal: num(raw.subtotal), delivery: num(raw.envio), total: num(raw.total), supermarketSaving: num(raw.ahorro_supermercado), balance: num(raw.saldo) };
}

export function toAccount(raw: Raw): Account {
  return { user: raw.usuario, name: raw.nombre, role: raw.rol, csrf: raw.csrf, zoneId: raw.zona, balance: raw.saldo !== undefined ? num(raw.saldo) : undefined, referralCode: raw.codigo_referido };
}

export function toZone(raw: Raw): Zone {
  return { id: raw.id, name: raw.nombre, district: raw.distrito, group: raw.grupo, status: raw.estado, lat: raw.lat, lon: raw.lon, admin: raw.admin, neighbors: raw.vecinos ?? 0, reception: raw.recibe ?? '', contact: raw.contacto ?? '' };
}

export function toCycle(raw: Raw): CycleState {
  return { cycle: raw.ciclo, open: Boolean(raw.abierto), closes: raw.cierre, delivery: raw.entrega, minimumOrder: num(raw.minimo_pedido), minimumGroup: num(raw.minimo_grupo) };
}

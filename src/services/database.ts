import { ID } from 'appwrite';
import { products as initialCatalog, windowLabel, zoneById } from '../data/catalog';
import type { AccountProfile, OrderLine, OrderRecord, OrderSelection, Product } from '../types';
import type { Quote } from '../utils/domain';
import { readStored, writeStored } from '../utils/storage';
import {
  appwriteReady,
  appwriteTables,
  databaseId,
  itemRowPermissions,
  orderRowPermissions,
  Query,
  tableIds,
} from './appwrite';

const LOCAL_CATALOG_KEY = 'yapa.catalog';
const LOCAL_ORDERS_KEY = 'yapa.orders';
const MANY = Query.limit(1000);

export interface CreateOrderInput {
  account: AccountProfile;
  selection: OrderSelection;
  lines: Array<{ product: Product; quantity: number }>;
  quote: Quote;
  cycleId: string;
  orderCode: string;
}

// campos que cambian después de registrar: cancelar, verificar, liquidar y devolver
export type OrderPatch = Partial<Pick<OrderRecord,
  'status' | 'paymentStatus' | 'finalTotal' | 'deliveryFinal' | 'refundToBalance' | 'refundToMethod' | 'refundPaidAt'>>;

function assertAppwrite() {
  if (!appwriteReady || !appwriteTables) throw new Error('Appwrite todavía no está configurado para este proyecto.');
  return appwriteTables;
}

function parseTiers(value: unknown, price: number) {
  try {
    const tiers = JSON.parse(String(value || '[]')) as Array<{ from: number; price: number }>;
    if (Array.isArray(tiers) && tiers.length) return [{ from: 0, price }, ...tiers.filter((tier) => tier.from > 0)];
  } catch {
    // sin tramos guardados: solo el precio máximo
  }
  return [{ from: 0, price }];
}

function mapProduct(row: Record<string, unknown>): Product {
  const price = Number(row.price);
  const fallback = initialCatalog.find((item) => item.id === String(row.id || row.$id));
  return {
    id: String(row.id || row.$id),
    name: String(row.name),
    category: String(row.category) as Product['category'],
    price,
    unit: String(row.unit),
    detail: String(row.detail),
    art: String(row.art) as Product['art'],
    image: String(row.image),
    stock: Number(row.stock),
    tiers: row.tiers ? parseTiers(row.tiers, price) : fallback ? [{ from: 0, price }, ...fallback.tiers.slice(1)] : [{ from: 0, price }],
  };
}

const ORDER_STATUSES = ['REGISTRADO', 'CANCELADO', 'ANULADO', 'LIQUIDADO', 'NO_ATENDIDO'];

function optionalNumber(value: unknown) {
  return value === null || value === undefined || value === '' ? undefined : Number(value);
}

function mapOrder(row: Record<string, unknown>, lines: OrderLine[] = []): OrderRecord {
  const zone = zoneById(String(row.zoneId || ''));
  const status = String(row.status);
  return {
    id: String(row.$id || row.id),
    userId: String(row.userId || ''),
    orderCode: String(row.orderCode),
    cycleId: String(row.cycleId || ''),
    zoneId: String(row.zoneId || ''),
    district: String(row.district || zone?.district || ''),
    reference: row.reference && row.reference !== '—' ? String(row.reference) : '',
    deliveryWindow: String(row.deliveryWindow || zone?.deliveryWindow || 'SAT_09_12') as OrderRecord['deliveryWindow'],
    paymentMethod: String(row.paymentMethod) as OrderRecord['paymentMethod'],
    operationCode: String(row.operationCode || ''),
    paymentStatus: row.paymentStatus === 'VERIFICADO' ? 'VERIFICADO' : 'POR_VERIFICAR',
    maxSubtotal: Number(row.maxSubtotal ?? row.total ?? 0),
    deliveryCharged: Number(row.deliveryCharged ?? 0),
    total: Number(row.total),
    paidExternal: Number(row.paidExternal ?? row.total ?? 0),
    paidBalance: Number(row.paidBalance ?? 0),
    status: (ORDER_STATUSES.includes(status) ? status : 'REGISTRADO') as OrderRecord['status'],
    itemCount: Number(row.itemCount || 0),
    createdAt: String(row.createdAt || row.$createdAt),
    lines,
    finalTotal: optionalNumber(row.finalTotal),
    deliveryFinal: optionalNumber(row.deliveryFinal),
    refundToBalance: Number(row.refundToBalance ?? 0),
    refundToMethod: Number(row.refundToMethod ?? 0),
    refundPaidAt: row.refundPaidAt ? String(row.refundPaidAt) : undefined,
  };
}

// catálogos guardados antes de los tramos: se completan con los del catálogo base
export function withTiers(product: Product): Product {
  const base = initialCatalog.find((item) => item.id === product.id);
  const rest = (product.tiers ?? base?.tiers ?? []).filter((tier) => tier.from > 0);
  return { ...product, tiers: [{ from: 0, price: product.price }, ...rest] };
}

function readLocalOrders() {
  return readStored<OrderRecord[]>(LOCAL_ORDERS_KEY, []);
}

export async function loadCatalog(): Promise<Product[]> {
  if (!appwriteReady) return readStored(LOCAL_CATALOG_KEY, initialCatalog).map(withTiers);
  const tables = assertAppwrite();
  const result = await tables.listRows({
    databaseId,
    tableId: tableIds.products,
    queries: [Query.equal('active', true), Query.orderAsc('name')],
  });
  const catalog = result.rows.map((row) => mapProduct(row as Record<string, unknown>));
  return catalog.length ? catalog : initialCatalog;
}

// el vecino ve sus pedidos; el admin ve todos, con sus líneas para poder liquidar
export async function loadOrders(userId: string | undefined, isAdmin = false): Promise<OrderRecord[]> {
  if (!appwriteReady) {
    const orders = readLocalOrders();
    return isAdmin ? orders : orders.filter((order) => order.userId === userId);
  }
  if (!userId) return [];
  const tables = assertAppwrite();
  const orderQueries = [Query.orderDesc('createdAt'), MANY];
  const itemQueries = [MANY];
  if (!isAdmin) {
    orderQueries.push(Query.equal('userId', userId));
    itemQueries.push(Query.equal('userId', userId));
  }
  const [orders, items] = await Promise.all([
    tables.listRows({ databaseId, tableId: tableIds.orders, queries: orderQueries }),
    tables.listRows({ databaseId, tableId: tableIds.orderItems, queries: itemQueries }),
  ]);
  const linesByOrder = new Map<string, OrderLine[]>();
  for (const raw of items.rows) {
    const item = raw as Record<string, unknown>;
    const lines = linesByOrder.get(String(item.orderId)) ?? [];
    lines.push({ productId: String(item.productId), productName: String(item.productName), quantity: Number(item.quantity), maxPrice: Number(item.unitPrice) });
    linesByOrder.set(String(item.orderId), lines);
  }
  let names = new Map<string, string>();
  if (isAdmin) {
    const profiles = await tables.listRows({ databaseId, tableId: tableIds.profiles, queries: [MANY] }).catch(() => null);
    names = new Map((profiles?.rows ?? []).map((row) => [String(row.$id), String((row as Record<string, unknown>).name || '')]));
  }
  return orders.rows.map((row) => {
    const order = mapOrder(row as Record<string, unknown>, linesByOrder.get(String(row.$id)));
    return { ...order, customerName: names.get(order.userId) };
  });
}

export async function createOrder(input: CreateOrderInput): Promise<OrderRecord> {
  const { account, selection, lines, quote, cycleId, orderCode } = input;
  const zone = zoneById(selection.zoneId);
  const paidBalance = selection.useBalance;
  const paidExternal = Math.round((quote.total - paidBalance) * 100) / 100;
  const record: OrderRecord = {
    id: '',
    userId: account.id,
    customerName: account.name,
    orderCode,
    cycleId,
    zoneId: selection.zoneId,
    district: zone?.district ?? account.district,
    reference: selection.reference.trim(),
    deliveryWindow: zone?.deliveryWindow ?? 'SAT_09_12',
    paymentMethod: paidExternal > 0 ? selection.paymentMethod : 'SALDO',
    operationCode: paidExternal > 0 ? selection.operationCode.trim() : '',
    paymentStatus: paidExternal > 0 ? 'POR_VERIFICAR' : 'VERIFICADO', // S-14: si el saldo cubre todo, se confirma al instante
    maxSubtotal: quote.subtotal,
    deliveryCharged: quote.delivery,
    total: quote.total,
    paidExternal,
    paidBalance,
    status: 'REGISTRADO',
    itemCount: lines.reduce((sum, line) => sum + line.quantity, 0),
    createdAt: new Date().toISOString(),
    lines: lines.map(({ product, quantity }) => ({ productId: product.id, productName: product.name, quantity, maxPrice: product.price })),
    refundToBalance: 0,
    refundToMethod: 0,
  };

  if (!appwriteReady) {
    const saved = { ...record, id: crypto.randomUUID() };
    writeStored(LOCAL_ORDERS_KEY, [saved, ...readLocalOrders()]);
    return saved;
  }

  const tables = assertAppwrite();
  const row = await tables.createRow({
    databaseId,
    tableId: tableIds.orders,
    rowId: ID.unique(),
    data: {
      userId: record.userId,
      orderCode: record.orderCode,
      cycleId: record.cycleId,
      zoneId: record.zoneId,
      district: record.district,
      addressLine: zone?.name ?? '',
      reference: record.reference || '—', // la columna es obligatoria
      latitude: zone?.coordinates.lat ?? 0,
      longitude: zone?.coordinates.lng ?? 0,
      deliveryWindow: record.deliveryWindow,
      paymentMethod: record.paymentMethod,
      operationCode: record.operationCode,
      paymentStatus: record.paymentStatus,
      maxSubtotal: record.maxSubtotal,
      deliveryCharged: record.deliveryCharged,
      paidExternal: record.paidExternal,
      paidBalance: record.paidBalance,
      refundToBalance: 0,
      refundToMethod: 0,
      status: record.status,
      total: record.total,
      itemCount: record.itemCount,
      createdAt: record.createdAt,
    },
    permissions: orderRowPermissions(account.id),
  });

  await Promise.all(record.lines.map((line) => tables.createRow({
    databaseId,
    tableId: tableIds.orderItems,
    rowId: ID.unique(),
    data: {
      orderId: row.$id,
      userId: account.id,
      productId: line.productId,
      productName: line.productName,
      quantity: line.quantity,
      unitPrice: line.maxPrice,
      createdAt: record.createdAt,
    },
    permissions: itemRowPermissions(account.id),
  })));

  return { ...record, id: row.$id };
}

export async function updateOrder(orderId: string, patch: OrderPatch): Promise<void> {
  if (!appwriteReady) {
    writeStored(LOCAL_ORDERS_KEY, readLocalOrders().map((order) => (order.id === orderId ? { ...order, ...patch } : order)));
    return;
  }
  const tables = assertAppwrite();
  try {
    await tables.updateRow({ databaseId, tableId: tableIds.orders, rowId: orderId, data: patch });
  } catch (error) {
    throw new Error(`No pudimos actualizar el pedido: ${error instanceof Error ? error.message : 'error desconocido'}`);
  }
}

export async function updateProduct(id: string, patch: Partial<Pick<Product, 'price' | 'stock'>>): Promise<void> {
  if (!appwriteReady) return;
  const tables = assertAppwrite();
  try {
    await tables.updateRow({ databaseId, tableId: tableIds.products, rowId: id, data: { ...patch, updatedAt: new Date().toISOString() } });
  } catch (error) {
    throw new Error(`No pudimos actualizar el producto: ${error instanceof Error ? error.message : 'error desconocido'}`);
  }
}

export function saveLocalCatalog(catalog: Product[]) {
  if (!appwriteReady) writeStored(LOCAL_CATALOG_KEY, catalog);
}

// solo en modo local: 10 vecinos de Jesús María (uno sin verificar) y 3 de Lince, para mostrar la liquidación
export function seedLocalDemo(catalog: Product[], cycleId: string): OrderRecord[] {
  const pick = (id: string) => catalog.find((product) => product.id === id) ?? initialCatalog.find((product) => product.id === id)!;
  const basket: Array<[string, number]> = [['papa-amarilla', 10], ['tomate-italiano', 2], ['leche-pack', 2]];
  const lines = basket.map(([id, quantity]) => ({ product: pick(id), quantity }));
  const subtotal = lines.reduce((sum, line) => sum + line.product.price * line.quantity, 0);
  const total = Math.floor((subtotal + 5) * 100 + 1e-6) / 100;
  const demo = (index: number, zoneId: string, verified: boolean): OrderRecord => {
    const zone = zoneById(zoneId)!;
    return {
      id: crypto.randomUUID(), userId: `demo-${index}`, customerName: `Vecino ${index}`, orderCode: `YP-D${String(index).padStart(3, '0')}`,
      cycleId, zoneId, district: zone.district, reference: `Dpto. ${100 + index}`, deliveryWindow: zone.deliveryWindow,
      paymentMethod: index % 2 ? 'YAPE' : 'PLIN', operationCode: `DEMO-${cycleId}-${index}`, paymentStatus: verified ? 'VERIFICADO' : 'POR_VERIFICAR',
      maxSubtotal: subtotal, deliveryCharged: 5, total, paidExternal: total, paidBalance: 0, status: 'REGISTRADO',
      itemCount: lines.reduce((sum, line) => sum + line.quantity, 0), createdAt: new Date().toISOString(),
      lines: lines.map(({ product, quantity }) => ({ productId: product.id, productName: product.name, quantity, maxPrice: product.price })),
      refundToBalance: 0, refundToMethod: 0,
    };
  };
  const seeded = [
    ...Array.from({ length: 10 }, (_, index) => demo(index + 1, 'Z-JM-01', index < 9)),
    ...Array.from({ length: 3 }, (_, index) => demo(index + 11, index < 2 ? 'Z-LINCE-01' : 'Z-LINCE-02', true)),
  ];
  const kept = readLocalOrders().filter((order) => !order.userId.startsWith('demo-'));
  const next = [...seeded, ...kept];
  writeStored(LOCAL_ORDERS_KEY, next);
  return next;
}

export { windowLabel };

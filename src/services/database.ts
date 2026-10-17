import { ID } from 'appwrite';
import { products as initialCatalog } from '../data/catalog';
import type { AccountProfile, OrderRecord, OrderSelection, Product } from '../types';
import { readStored, writeStored } from '../utils/storage';
import {
  appwriteReady,
  appwriteTables,
  databaseId,
  orderRowPermissions,
  Query,
  tableIds,
  userRowPermissions,
} from './appwrite';

const LOCAL_CATALOG_KEY = 'yapa.catalog';
const LOCAL_ORDERS_KEY = 'yapa.orders';

export interface CreateOrderInput {
  account: AccountProfile;
  selection: OrderSelection;
  lines: Array<{ product: Product; quantity: number }>;
  total: number;
  orderCode: string;
}

function assertAppwrite() {
  if (!appwriteReady || !appwriteTables) throw new Error('Appwrite todavía no está configurado para este proyecto.');
  return appwriteTables;
}

function mapProduct(row: Record<string, unknown>): Product {
  return {
    id: String(row.id || row.$id),
    name: String(row.name),
    category: String(row.category) as Product['category'],
    price: Number(row.price),
    unit: String(row.unit),
    detail: String(row.detail),
    art: String(row.art) as Product['art'],
    image: String(row.image),
    stock: Number(row.stock),
  };
}

function mapOrder(row: Record<string, unknown>): OrderRecord {
  return {
    id: String(row.$id || row.id),
    userId: row.userId ? String(row.userId) : undefined,
    orderCode: String(row.orderCode),
    district: String(row.district),
    addressLine: String(row.addressLine),
    reference: row.reference ? String(row.reference) : '',
    coordinates: { lat: Number(row.latitude), lng: Number(row.longitude) },
    deliveryWindow: String(row.deliveryWindow),
    paymentMethod: String(row.paymentMethod) as OrderRecord['paymentMethod'],
    total: Number(row.total),
    itemCount: Number(row.itemCount || 0),
    createdAt: String(row.createdAt || row.$createdAt),
    status: String(row.status) as OrderRecord['status'],
  };
}

export async function loadCatalog(): Promise<Product[]> {
  if (!appwriteReady) return readStored(LOCAL_CATALOG_KEY, initialCatalog);
  const tables = assertAppwrite();
  const result = await tables.listRows({
    databaseId,
    tableId: tableIds.products,
    queries: [Query.equal('active', true), Query.orderAsc('name')],
  });
  const catalog = result.rows.map((row) => mapProduct(row as Record<string, unknown>));
  return catalog.length ? catalog : initialCatalog;
}

export async function loadOrders(userId: string | undefined, isAdmin = false): Promise<OrderRecord[]> {
  if (!appwriteReady) {
    const orders = readStored<OrderRecord[]>(LOCAL_ORDERS_KEY, []);
    return isAdmin ? orders : orders.filter((order) => order.userId === userId);
  }
  if (!userId) return [];
  const tables = assertAppwrite();
  const queries = [Query.orderDesc('createdAt')];
  if (!isAdmin) queries.push(Query.equal('userId', userId));
  const result = await tables.listRows({ databaseId, tableId: tableIds.orders, queries });
  return result.rows.map((row) => mapOrder(row as Record<string, unknown>));
}

export async function createOrder(input: CreateOrderInput): Promise<OrderRecord> {
  const { account, selection, lines, total, orderCode } = input;
  const itemCount = lines.reduce((sum, line) => sum + line.quantity, 0);
  const createdAt = new Date().toISOString();

  if (appwriteReady) {
    const tables = assertAppwrite();
    const order = await tables.createRow({
      databaseId,
      tableId: tableIds.orders,
      rowId: ID.unique(),
      data: {
        userId: account.id,
        orderCode,
        district: selection.district,
        addressLine: selection.addressLine,
        reference: selection.reference,
        latitude: selection.coordinates.lat,
        longitude: selection.coordinates.lng,
        deliveryWindow: selection.deliveryWindow,
        paymentMethod: selection.paymentMethod,
        status: 'RECIBIDO',
        total,
        itemCount,
        createdAt,
      },
      permissions: orderRowPermissions(account.id),
    });

    await tables.createRow({
      databaseId,
      tableId: tableIds.addresses,
      rowId: ID.unique(),
      data: {
        userId: account.id,
        district: selection.district,
        addressLine: selection.addressLine,
        reference: selection.reference,
        latitude: selection.coordinates.lat,
        longitude: selection.coordinates.lng,
        createdAt,
      },
      permissions: userRowPermissions(account.id),
    });

    await Promise.all(lines.map(({ product, quantity }) => tables.createRow({
      databaseId,
      tableId: tableIds.orderItems,
      rowId: ID.unique(),
      data: {
        orderId: order.$id,
        userId: account.id,
        productId: product.id,
        productName: product.name,
        quantity,
        unitPrice: product.price,
        createdAt,
      },
      permissions: orderRowPermissions(account.id),
    })));

    return mapOrder(order as unknown as Record<string, unknown>);
  }

  const nextOrder: OrderRecord = { ...selection, id: crypto.randomUUID(), userId: account.id, orderCode, total, itemCount, createdAt, status: 'RECIBIDO' };
  const orders = readStored<OrderRecord[]>(LOCAL_ORDERS_KEY, []);
  writeStored(LOCAL_ORDERS_KEY, [nextOrder, ...orders]);
  return nextOrder;
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

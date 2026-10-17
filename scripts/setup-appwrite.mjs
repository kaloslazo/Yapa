import fs from 'node:fs';
import process from 'node:process';
import { Client, Permission, Role, TablesDB, Users } from 'node-appwrite';

function loadEnvFile(path) {
  if (!fs.existsSync(path)) return;
  for (const line of fs.readFileSync(path, 'utf8').split(/\r?\n/)) {
    const match = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/);
    if (!match || process.env[match[1]]) continue;
    process.env[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
  }
}

loadEnvFile('.env.local');
loadEnvFile('.env');

const endpoint = process.env.APPWRITE_ENDPOINT || process.env.VITE_APPWRITE_ENDPOINT || 'https://cloud.appwrite.io/v1';
const projectId = process.env.APPWRITE_PROJECT_ID || process.env.VITE_APPWRITE_PROJECT_ID;
const apiKey = process.env.APPWRITE_API_KEY;
const databaseId = process.env.APPWRITE_DATABASE_ID || process.env.VITE_APPWRITE_DATABASE_ID || 'yapa';
const adminUserId = process.env.APPWRITE_ADMIN_USER_ID;
const adminLabel = process.env.APPWRITE_ADMIN_LABEL || process.env.VITE_APPWRITE_ADMIN_LABEL || 'admin';

if (!projectId || !apiKey) {
  console.error('Faltan APPWRITE_PROJECT_ID y APPWRITE_API_KEY. Guárdalos en .env.local o pásalos al ejecutar el script.');
  process.exit(1);
}

const client = new Client().setEndpoint(endpoint).setProject(projectId).setKey(apiKey);
const tables = new TablesDB(client);
const users = new Users(client);

function isConflict(error) {
  return typeof error === 'object' && error !== null && 'code' in error && error.code === 409;
}

function isNotFound(error) {
  return typeof error === 'object' && error !== null && 'code' in error && error.code === 404;
}

async function ensure(label, create) {
  try {
    await create();
    console.log(`✓ ${label}`);
  } catch (error) {
    if (isConflict(error)) {
      console.log(`↺ ${label} ya existe`);
      return;
    }
    throw error;
  }
}

const adminRead = Permission.read(Role.label(adminLabel));
const adminCreate = Permission.create(Role.label(adminLabel));
const adminUpdate = Permission.update(Role.label(adminLabel));
const adminDelete = Permission.delete(Role.label(adminLabel));
const userCreate = Permission.create(Role.users());

const tableDefinitions = [
  {
    id: 'profiles',
    name: 'Perfiles',
    permissions: [userCreate, adminRead, adminUpdate],
    rowSecurity: true,
    columns: [
      { key: 'email', type: 'email', required: true },
      { key: 'name', type: 'string', size: 128, required: true },
      { key: 'phone', type: 'string', size: 32, required: true },
      { key: 'district', type: 'string', size: 64, required: true },
      { key: 'zoneId', type: 'string', size: 32, required: false },
      { key: 'role', type: 'string', size: 32, required: true },
      { key: 'createdAt', type: 'datetime', required: true },
    ],
  },
  {
    id: 'products',
    name: 'Productos',
    permissions: [Permission.read(Role.any()), adminCreate, adminUpdate, adminDelete],
    rowSecurity: false,
    columns: [
      { key: 'id', type: 'string', size: 64, required: true },
      { key: 'name', type: 'string', size: 128, required: true },
      { key: 'category', type: 'string', size: 64, required: true },
      { key: 'price', type: 'double', required: true },
      { key: 'unit', type: 'string', size: 64, required: true },
      { key: 'detail', type: 'string', size: 256, required: true },
      { key: 'art', type: 'string', size: 64, required: true },
      { key: 'image', type: 'string', size: 512, required: true },
      { key: 'stock', type: 'integer', required: true },
      { key: 'active', type: 'boolean', required: true },
      { key: 'tiers', type: 'string', size: 512, required: false },
      { key: 'updatedAt', type: 'datetime', required: true },
    ],
  },
  {
    id: 'addresses',
    name: 'Direcciones',
    permissions: [userCreate, adminRead],
    rowSecurity: true,
    columns: [
      { key: 'userId', type: 'string', size: 36, required: true },
      { key: 'district', type: 'string', size: 64, required: true },
      { key: 'addressLine', type: 'string', size: 256, required: true },
      { key: 'reference', type: 'string', size: 256, required: true },
      { key: 'latitude', type: 'double', required: true },
      { key: 'longitude', type: 'double', required: true },
      { key: 'createdAt', type: 'datetime', required: true },
    ],
  },
  {
    id: 'orders',
    name: 'Pedidos',
    permissions: [userCreate, adminRead, adminUpdate],
    rowSecurity: true,
    columns: [
      { key: 'userId', type: 'string', size: 36, required: true },
      { key: 'orderCode', type: 'string', size: 32, required: true },
      { key: 'district', type: 'string', size: 64, required: true },
      { key: 'addressLine', type: 'string', size: 256, required: true },
      { key: 'reference', type: 'string', size: 256, required: true },
      { key: 'latitude', type: 'double', required: true },
      { key: 'longitude', type: 'double', required: true },
      { key: 'deliveryWindow', type: 'string', size: 64, required: true },
      { key: 'paymentMethod', type: 'string', size: 64, required: true },
      { key: 'status', type: 'string', size: 32, required: true },
      { key: 'total', type: 'double', required: true },
      { key: 'itemCount', type: 'integer', required: true },
      { key: 'createdAt', type: 'datetime', required: true },
      { key: 'cycleId', type: 'string', size: 16, required: false },
      { key: 'zoneId', type: 'string', size: 32, required: false },
      { key: 'operationCode', type: 'string', size: 64, required: false },
      { key: 'paymentStatus', type: 'string', size: 32, required: false },
      { key: 'maxSubtotal', type: 'double', required: false },
      { key: 'deliveryCharged', type: 'double', required: false },
      { key: 'paidExternal', type: 'double', required: false },
      { key: 'paidBalance', type: 'double', required: false },
      { key: 'finalTotal', type: 'double', required: false },
      { key: 'deliveryFinal', type: 'double', required: false },
      { key: 'refundToBalance', type: 'double', required: false },
      { key: 'refundToMethod', type: 'double', required: false },
      { key: 'refundPaidAt', type: 'datetime', required: false },
    ],
  },
  {
    id: 'order_items',
    name: 'Detalle de pedidos',
    permissions: [userCreate, adminRead],
    rowSecurity: true,
    columns: [
      { key: 'orderId', type: 'string', size: 36, required: true },
      { key: 'userId', type: 'string', size: 36, required: true },
      { key: 'productId', type: 'string', size: 64, required: true },
      { key: 'productName', type: 'string', size: 128, required: true },
      { key: 'quantity', type: 'integer', required: true },
      { key: 'unitPrice', type: 'double', required: true },
      { key: 'createdAt', type: 'datetime', required: true },
    ],
  },
];

try {
  await tables.get({ databaseId });
  console.log(`↺ base de datos ${databaseId} ya existe`);
} catch (error) {
  if (!isNotFound(error)) throw error;
  await ensure(`base de datos ${databaseId}`, () => tables.create({ databaseId, name: 'Yapa', enabled: true }));
}

const createColumn = {
  string: (base, column) => tables.createStringColumn({ ...base, size: column.size }),
  email: (base) => tables.createEmailColumn(base),
  double: (base) => tables.createFloatColumn(base),
  integer: (base) => tables.createIntegerColumn(base),
  boolean: (base) => tables.createBooleanColumn(base),
  datetime: (base) => tables.createDatetimeColumn(base),
};

// las tablas creadas antes no reciben columnas nuevas solas: se agregan las que falten
async function syncTable(table) {
  await tables.updateTable({ databaseId, tableId: table.id, name: table.name, permissions: table.permissions, rowSecurity: table.rowSecurity, enabled: true });
  const existing = await tables.listColumns({ databaseId, tableId: table.id });
  const keys = new Set(existing.columns.map((column) => column.key));
  const missing = table.columns.filter((column) => !keys.has(column.key));
  for (const column of missing) {
    await createColumn[column.type]({ databaseId, tableId: table.id, key: column.key, required: column.required }, column);
    console.log(`✓ columna ${table.id}.${column.key}`);
  }
  for (let attempt = 0; missing.length && attempt < 30; attempt += 1) {
    const { columns } = await tables.listColumns({ databaseId, tableId: table.id });
    if (missing.every((column) => columns.some((item) => item.key === column.key && item.status === 'available'))) break;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
}

for (const table of tableDefinitions) {
  await ensure(`tabla ${table.id}`, () => tables.createTable({
    databaseId,
    tableId: table.id,
    name: table.name,
    permissions: table.permissions,
    rowSecurity: table.rowSecurity,
    enabled: true,
    columns: table.columns,
  }));
  await syncTable(table);
}

// precios de ejemplo: el primero es el máximo; `tiers` son los tramos que bajan con el volumen de todos
const products = [
  ['arroz-extra', 'Arroz extra', 'Despensa', 4.8, 'kg', 'Grano largo, calidad mayorista', 'rice', '/images/products/arroz-extra.png', 300, [[100, 4.5], [250, 4.3]]],
  ['aceite-vegetal', 'Aceite vegetal', 'Despensa', 8.9, 'L', 'Botella familiar de 1 litro', 'oil', '/images/products/aceite-vegetal.png', 120, [[24, 8.4]]],
  ['platano-seda', 'Plátano de seda', 'Frutas', 3.9, 'kg', 'Dulce y listo para la semana', 'banana', '/images/products/platano-seda.png', 150, [[60, 3.5]]],
  ['tomate-italiano', 'Tomate italiano', 'Verduras', 5.6, 'kg', 'Cosecha seleccionada del día', 'tomato', '/images/products/tomate-italiano.png', 200, [[80, 4.9]]],
  ['papa-amarilla', 'Papa amarilla', 'Verduras', 4.2, 'kg', 'Textura cremosa para guisos', 'potato', '/images/products/papa-amarilla.png', 400, [[100, 3.9], [250, 3.7]]],
  ['leche-pack', 'Leche evaporada', 'Lácteos', 21.6, 'pack x 6', 'Seis latas para la despensa', 'milk', '/images/products/leche-pack.png', 60, [[12, 20.4]]],
];

const now = new Date().toISOString();
for (const [id, name, category, price, unit, detail, art, image, stock, tierPairs] of products) {
  const tiers = JSON.stringify(tierPairs.map(([from, tierPrice]) => ({ from, price: tierPrice })));
  await tables.upsertRow({
    databaseId,
    tableId: 'products',
    rowId: id,
    data: { id, name, category, price, unit, detail, art, image, stock, tiers, active: true, updatedAt: now },
  });
}
console.log(`✓ ${products.length} productos iniciales listos`);

if (adminUserId) {
  const user = await users.get({ userId: adminUserId });
  await users.updateLabels({ userId: adminUserId, labels: [adminLabel] });
  await tables.upsertRow({
    databaseId,
    tableId: 'profiles',
    rowId: adminUserId,
    data: {
      email: user.email,
      name: user.name || 'Admin Yapa',
      phone: '',
      district: 'Lince',
      role: 'admin',
      createdAt: now,
    },
    permissions: [Permission.read(Role.user(adminUserId)), Permission.update(Role.user(adminUserId)), adminRead, adminUpdate],
  });
  console.log(`✓ usuario ${adminUserId} marcado como administrador con la etiqueta ${adminLabel}`);
}

console.log('\nAppwrite quedó preparado. Si aún no existe el administrador, crea el usuario en Auth y vuelve a ejecutar este script con APPWRITE_ADMIN_USER_ID.');

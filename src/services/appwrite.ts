import { Account, Client, Permission, Query, Role, TablesDB } from 'appwrite';

const endpoint = import.meta.env.VITE_APPWRITE_ENDPOINT || 'https://cloud.appwrite.io/v1';
const projectId = import.meta.env.VITE_APPWRITE_PROJECT_ID || '';

export const databaseId = import.meta.env.VITE_APPWRITE_DATABASE_ID || 'yapa';
export const adminLabel = import.meta.env.VITE_APPWRITE_ADMIN_LABEL || 'admin';
export const tableIds = {
  profiles: import.meta.env.VITE_APPWRITE_PROFILES_TABLE_ID || 'profiles',
  products: import.meta.env.VITE_APPWRITE_PRODUCTS_TABLE_ID || 'products',
  addresses: import.meta.env.VITE_APPWRITE_ADDRESSES_TABLE_ID || 'addresses',
  orders: import.meta.env.VITE_APPWRITE_ORDERS_TABLE_ID || 'orders',
  orderItems: import.meta.env.VITE_APPWRITE_ORDER_ITEMS_TABLE_ID || 'order_items',
};

export const appwriteConfigured = Boolean(projectId);
export const appwriteReady = Boolean(projectId && databaseId && Object.values(tableIds).every(Boolean));

export const appwriteClient = appwriteConfigured
  ? new Client().setEndpoint(endpoint).setProject(projectId)
  : null;

export const appwriteAccount = appwriteClient ? new Account(appwriteClient) : null;
export const appwriteTables = appwriteClient ? new TablesDB(appwriteClient) : null;
export const persistenceMode: 'appwrite' | 'local' = appwriteReady ? 'appwrite' : 'local';

// Un cliente solo puede dar permisos a roles que él mismo tiene (user:<id>, users, any).
// El acceso del admin va en los permisos de cada tabla (scripts/setup-appwrite.mjs).
export function profilePermissions(userId: string) {
  return [Permission.read(Role.user(userId)), Permission.update(Role.user(userId))];
}

export function userRowPermissions(userId: string) {
  return [
    Permission.read(Role.user(userId)),
    Permission.update(Role.user(userId)),
    Permission.delete(Role.user(userId)),
  ];
}

// el vecino puede actualizar su pedido para cancelarlo antes del cierre
export function orderRowPermissions(userId: string) {
  return [Permission.read(Role.user(userId)), Permission.update(Role.user(userId))];
}

export function itemRowPermissions(userId: string) {
  return [Permission.read(Role.user(userId))];
}

export function adminRowPermissions() {
  return [
    Permission.read(Role.label(adminLabel)),
    Permission.update(Role.label(adminLabel)),
    Permission.delete(Role.label(adminLabel)),
  ];
}

export { Permission, Query, Role };

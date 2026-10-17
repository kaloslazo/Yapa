/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APPWRITE_ENDPOINT?: string;
  readonly VITE_APPWRITE_PROJECT_ID?: string;
  readonly VITE_APPWRITE_DATABASE_ID?: string;
  readonly VITE_APPWRITE_PROFILES_TABLE_ID?: string;
  readonly VITE_APPWRITE_PRODUCTS_TABLE_ID?: string;
  readonly VITE_APPWRITE_ADDRESSES_TABLE_ID?: string;
  readonly VITE_APPWRITE_ORDERS_TABLE_ID?: string;
  readonly VITE_APPWRITE_ORDER_ITEMS_TABLE_ID?: string;
  readonly VITE_APPWRITE_ADMIN_LABEL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

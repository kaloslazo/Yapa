// tipos de la tienda; los datos vienen de la API del motor (api/, iteración 27)

export type ProductArtName = 'rice' | 'oil' | 'banana' | 'tomato' | 'potato' | 'milk';
export type CartState = Record<string, number>;

export interface PriceTier {
  from: number;
  price: number;
}

export interface ReferencePrice {
  kind: 'MERCADO' | 'SUPERMERCADO';
  source: string;
  price: number;
  seen: string;
}

export interface Product {
  id: string;
  name: string;
  category: string; // nombre para mostrar: Frescos, Limpieza
  price: number; // precio máximo, lo que se paga al pedir (C-01)
  unit: string;
  step: number;
  maxPerOrder: number;
  ordered: number; // lo pedido entre todos en el ciclo
  nextTier: PriceTier | null;
  tiers: PriceTier[];
  references: ReferencePrice[];
  supermarket: ReferencePrice | null;
  supermarketSaving: number | null; // % de ahorro del precio máximo frente al supermercado
  detail: string;
  art: ProductArtName;
  image: string | null;
  emoji: string;
}

export type Role = 'vecino' | 'admin_zona' | 'admin' | 'transportista' | 'proveedor';

export interface Account {
  user: string | number;
  name: string;
  role: Role;
  csrf: string;
  zoneId?: string;
  balance?: number;
  referralCode?: string;
  email?: string | null;
  emailVerified?: boolean;
  googleLinked?: boolean;
  hasPin?: boolean;
  viewingAs?: string;
  canViewAs?: boolean;
  supplierId?: string | null;
}

export interface Zone {
  id: string;
  name: string;
  district: string;
  group: string;
  status: 'ACTIVA' | 'PENDIENTE_RECEPCION';
  lat: number | null;
  lon: number | null;
  admin: number | null;
  neighbors: number;
  reception: string;
  contact: string;
}

export interface OrderLine {
  id: string;
  name: string;
  quantity: number;
  maxPrice: number;
  total: number;
}

export interface Settlement {
  status: string;
  paid: number;
  cost: number;
  returned: number;
  destination: string | null;
  benefit: number;
  comparison: Partial<Record<'MERCADO' | 'SUPERMERCADO', { before: number; saving: number }>>;
}

export interface Order {
  id: number;
  cycle: string;
  zoneId: string;
  customer: number;
  customerName?: string;
  status: string;
  payment: 'POR_VERIFICAR' | 'VERIFICADO';
  method: string;
  paymentCode: string;
  total: number;
  subtotal: number;
  delivery: number;
  withBalance: number;
  toPay: number;
  delivered: boolean;
  cancellable: boolean;
  lines: OrderLine[];
  settlement: Settlement | null;
  bags?: Array<{ number: number; photo: string }>;
}

export interface Quote {
  lines: OrderLine[];
  subtotal: number;
  delivery: number;
  total: number;
  supermarketSaving: number;
  balance: number;
}

export interface CycleState {
  cycle: string;
  open: boolean;
  closes: string;
  delivery: string;
  minimumOrder: number;
  minimumGroup: number;
}

export type RefundDestination = 'SALDO' | 'MEDIO_DE_PAGO';

export interface Notice {
  id: number;
  kind: string;
  title: string;
  text: string;
  at: string;
  read: boolean;
}

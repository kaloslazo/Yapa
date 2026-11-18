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
  jug: [string, string] | null; // galones sin foto: color del líquido y de la tapa
  group: 'tuberculos' | 'verduras' | 'limpieza'; // grupo para mostrar en la tienda
  tint: string; // pastel detrás de la foto
  emoji: string;
}

export type StaffRole = 'compras' | 'armador' | 'atencion';
export type Role = 'vecino' | 'admin_zona' | 'admin' | 'transportista' | 'proveedor' | 'porteria' | StaffRole;

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
  unit?: string; // UN-01: kg o unidad
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
  zoneName?: string; // OC-05: nombre del edificio para el panel
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
  bags?: Array<{ number: number; photo: string; products?: Array<{ id: string; units: number }> }>;
  labels?: string[]; // S-298: rótulo de cada bolsa
  tracking?: TrackingStep[]; // S-309, S-312: los siete pasos con hora y detalle
  trackingStatus?: { title: string; detail: string }; // S-311: el estado en una frase
  photos?: { delivery: boolean; bags: number }; // S-313: fotos del propio pedido
  payTo?: { number: string; holder: string }; // S-305: el Plin de Yapa
}

export interface TrackingStep {
  step: string;
  done: boolean;
  when?: string | null;
  detail?: string;
}

// iteración 60: canasta sugerida por la IA; los precios los pone el motor
export interface BasketSuggestion {
  lines: Array<{ id: string; name: string; unit: string; quantity: number; maxPrice: number; total: number }>;
  subtotal: number;
  missing: number;
  comment: string;
  provider: string;
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
  ai: boolean; // IA-01: el servidor tiene la IA activada
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

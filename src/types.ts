export const categories = ['Todos', 'Despensa', 'Frutas', 'Verduras', 'Lácteos'] as const;
export type Category = (typeof categories)[number];

// precio por tramo: desde `from` unidades pedidas entre todos, el precio baja a `price`
export interface PriceTier {
  from: number;
  price: number;
}

export interface Product {
  id: string;
  name: string;
  category: Exclude<Category, 'Todos'>;
  price: number; // precio máximo (primer tramo), lo que se paga al pedir
  unit: string;
  detail: string;
  art: ProductArtName;
  image: string;
  stock: number; // lo máximo que el proveedor puede vender este ciclo (C-12)
  tiers: PriceTier[];
}

export type ProductArtName = 'rice' | 'oil' | 'banana' | 'tomato' | 'potato' | 'milk';
export type CartState = Record<string, number>;

export type DeliveryWindowCode = 'SAT_09_12' | 'SAT_12_15' | 'SAT_15_18';

export interface DeliveryWindow {
  code: DeliveryWindowCode;
  label: string;
}

// zona = punto de recepción (portería o encargado); las zonas de un grupo suman para el mínimo (C-07)
export interface Zone {
  id: string;
  name: string;
  district: string;
  groupId: string;
  stopCost: number;
  deliveryWindow: DeliveryWindowCode;
  active: boolean;
  coordinates: { lat: number; lng: number };
}

export type PaymentMethodValue = 'YAPE' | 'PLIN';

export interface PaymentMethod {
  value: PaymentMethodValue;
  label: string;
}

export type AccountRole = 'customer' | 'admin';

export interface AccountProfile {
  id: string;
  name: string;
  phone: string;
  district: string;
  zoneId: string;
  email: string;
  role: AccountRole;
}

export interface OrderSelection {
  zoneId: string;
  reference: string;
  paymentMethod: PaymentMethodValue;
  operationCode: string;
  useBalance: number;
}

export type OrderStatus = 'REGISTRADO' | 'CANCELADO' | 'ANULADO' | 'LIQUIDADO' | 'NO_ATENDIDO';
export type PaymentStatus = 'POR_VERIFICAR' | 'VERIFICADO';
export type RefundDestination = 'SALDO' | 'MEDIO_DE_PAGO';

export interface OrderLine {
  productId: string;
  productName: string;
  quantity: number;
  maxPrice: number;
}

export interface OrderRecord {
  id: string;
  userId: string;
  customerName?: string;
  orderCode: string;
  cycleId: string;
  zoneId: string;
  district: string;
  reference: string;
  deliveryWindow: DeliveryWindowCode;
  paymentMethod: PaymentMethodValue | 'SALDO';
  operationCode: string;
  paymentStatus: PaymentStatus;
  maxSubtotal: number;
  deliveryCharged: number;
  total: number; // lo que pagó al pedir: precio máximo más envío máximo
  paidExternal: number; // por Yape o Plin
  paidBalance: number; // con su saldo
  status: OrderStatus;
  itemCount: number;
  createdAt: string;
  lines: OrderLine[];
  finalTotal?: number; // lo que costó de verdad, al liquidar
  deliveryFinal?: number;
  refundToBalance: number; // lo que volvió a su saldo
  refundToMethod: number; // lo que se le devuelve a su Yape o Plin
  refundPaidAt?: string;
}

export type OrderConfirmation = OrderRecord;

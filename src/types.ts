export const categories = ['Todos', 'Despensa', 'Frutas', 'Verduras', 'Lácteos'] as const;
export type Category = (typeof categories)[number];

export interface Product {
  id: string;
  name: string;
  category: Exclude<Category, 'Todos'>;
  price: number;
  unit: string;
  detail: string;
  art: ProductArtName;
  image: string;
  stock: number;
}

export type ProductArtName = 'rice' | 'oil' | 'banana' | 'tomato' | 'potato' | 'milk';
export type CartState = Record<string, number>;

export interface DeliveryWindow {
  code: string;
  label: string;
  capacity: string;
}

export type PaymentMethodValue = 'TRANSFERENCIA' | 'BILLETERA_DIGITAL' | 'CONTRAENTREGA';

export type AccountRole = 'customer' | 'admin';

export interface AccountProfile {
  id: string;
  name: string;
  phone: string;
  district: string;
  email: string;
  role: AccountRole;
}

export interface PaymentMethod {
  value: PaymentMethodValue;
  label: string;
  note: string;
}

export interface OrderSelection {
  district: string;
  deliveryWindow: string;
  paymentMethod: PaymentMethodValue;
  addressLine: string;
  reference: string;
  coordinates: { lat: number; lng: number };
}

export interface OrderConfirmation extends OrderSelection {
  orderCode: string;
}

export type OrderStatus = 'RECIBIDO' | 'PREPARANDO' | 'EN RUTA' | 'ENTREGADO';

export interface OrderRecord extends OrderConfirmation {
  id?: string;
  userId?: string;
  total: number;
  itemCount: number;
  createdAt: string;
  status: OrderStatus;
}

import type { OrderLine, OrderRecord, PaymentMethodValue, Product, RefundDestination, Zone } from '../types';

// reglas del modelo nuevo (decisiones C-01..C-12 y supuestos S-01..S-12 del equipo)
export const MIN_SUBTOTAL = 50; // S-04
export const MAX_DELIVERY_FEE = 5; // S-05
export const MIN_ORDERS_PER_GROUP = 8; // S-06
export const SUPPORTED_DISTRICTS = ['Lince', 'Jesús María', 'La Victoria'] as const; // S-01
export const PAYMENT_METHODS: PaymentMethodValue[] = ['YAPE', 'PLIN']; // C-03

// S-08: por kg hasta 10, por unidad hasta 6
export function maxPerLine(product: Product): number {
  return product.unit === 'kg' ? 10 : 6;
}

// S-09: los cobros se redondean al céntimo a favor del cliente
export function floorCents(value: number): number {
  return Math.floor(value * 100 + 1e-6) / 100;
}

export function roundCents(value: number): number {
  return Math.round(value * 100) / 100;
}

// ciclo semanal en hora de Lima (UTC-5 todo el año, S-02)
const LIMA_OFFSET_MS = -5 * 60 * 60 * 1000;

function limaParts(moment: Date) {
  const local = new Date(moment.getTime() + LIMA_OFFSET_MS);
  return { date: local, weekday: local.getUTCDay() || 7, hours: local.getUTCHours() };
}

export function cycleId(moment: Date): string {
  const { date, weekday } = limaParts(moment);
  const thursday = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() + 4 - weekday));
  const yearStart = Date.UTC(thursday.getUTCFullYear(), 0, 1);
  const week = Math.ceil(((thursday.getTime() - yearStart) / 86400000 + 1) / 7);
  return `${thursday.getUTCFullYear()}-W${String(week).padStart(2, '0')}`;
}

// abierto desde el lunes 00:00 hasta antes del miércoles 20:00
export function isCycleOpen(moment: Date): boolean {
  const { weekday, hours } = limaParts(moment);
  return weekday === 1 || weekday === 2 || (weekday === 3 && hours < 20);
}

// C-01: el precio que se paga al pedir es el máximo (primer tramo)
export function maxPrice(product: Product): number {
  return product.price;
}

export function tierFor(product: Product, totalQuantity: number) {
  const reached = product.tiers.filter((tier) => tier.from <= totalQuantity);
  return reached.length ? reached.reduce((best, tier) => (tier.from > best.from ? tier : best)) : product.tiers[0];
}

export function nextTier(product: Product, totalQuantity = 0) {
  return product.tiers.find((tier) => tier.from > totalQuantity) ?? null;
}

export interface Quote {
  subtotal: number;
  delivery: number;
  total: number;
}

// lo que se paga hoy: precio máximo más envío máximo (C-02, C-09)
export function quoteOrder(lines: Array<{ product: Product; quantity: number }>): Quote {
  const subtotal = lines.reduce((sum, { product, quantity }) => sum + maxPrice(product) * quantity, 0);
  if (!lines.length) return { subtotal: 0, delivery: 0, total: 0 };
  return { subtotal, delivery: MAX_DELIVERY_FEE, total: floorCents(subtotal + MAX_DELIVERY_FEE) };
}

export function canCheckout(subtotal: number): boolean {
  return subtotal >= MIN_SUBTOTAL; // se compara el valor exacto
}

// C-05: el saldo es lo que volvió a favor menos lo que ya se usó en pedidos
export function balanceOf(orders: OrderRecord[]): number {
  return roundCents(orders.reduce((sum, order) => sum + order.refundToBalance - order.paidBalance, 0));
}

export interface CheckoutCheck {
  subtotal: number;
  total: number;
  zone: Zone | undefined;
  now: Date;
  orders: OrderRecord[]; // pedidos del propio vecino
  paymentMethod: string;
  operationCode: string;
  useBalance: number;
}

// errores en el orden fijo de S-11: zona, ciclo, pedido existente, subtotal, saldo, pago
export function validateCheckout(input: CheckoutCheck): string | null {
  const { zone, now, orders } = input;
  if (!zone || !zone.active || !SUPPORTED_DISTRICTS.includes(zone.district as (typeof SUPPORTED_DISTRICTS)[number])) {
    return 'Tu zona todavía no recibe pedidos. Elige una zona activa.';
  }
  if (!isCycleOpen(now)) return 'El ciclo semanal está cerrado. Vuelve el lunes.';
  const current = cycleId(now);
  if (orders.some((order) => order.cycleId === current && order.status === 'REGISTRADO')) {
    return 'Ya tienes un pedido en este ciclo. Puedes cancelarlo desde Mis pedidos para hacer otro.'; // S-03
  }
  if (!canCheckout(input.subtotal)) return `El pedido mínimo es S/ ${MIN_SUBTOTAL.toFixed(2)}. Te faltan S/ ${(MIN_SUBTOTAL - input.subtotal).toFixed(2)}.`;
  const balance = balanceOf(orders);
  if (input.useBalance < 0 || input.useBalance > balance + 1e-9) return 'No tienes saldo suficiente.';
  if (input.useBalance > input.total + 1e-9) return 'El saldo a usar no puede pasar del total.';
  const external = roundCents(input.total - input.useBalance);
  if (external > 0) {
    if (!PAYMENT_METHODS.includes(input.paymentMethod as PaymentMethodValue)) return 'Solo se acepta Yape o Plin.';
    const code = input.operationCode.trim();
    if (!code) return 'Ingresa el código de operación de tu Yape o Plin.';
    if (orders.some((order) => order.operationCode === code)) return 'Ese código de operación ya fue usado en otro pedido.'; // C-04
  }
  return null;
}

export function canCancel(order: OrderRecord, now: Date): boolean {
  return order.status === 'REGISTRADO' && isCycleOpen(now) && order.cycleId === cycleId(now);
}

// cancelar antes del cierre: vuelve todo; un Yape sin verificar lo revisa el equipo (S-20)
export function cancelOrder(order: OrderRecord, destination: RefundDestination): Pick<OrderRecord, 'status' | 'refundToBalance' | 'refundToMethod'> {
  const verified = order.paymentStatus === 'VERIFICADO';
  return {
    status: 'CANCELADO',
    refundToBalance: roundCents(order.paidBalance + (verified && destination === 'SALDO' ? order.paidExternal : 0)),
    refundToMethod: verified && destination === 'MEDIO_DE_PAGO' ? order.paidExternal : 0,
  };
}

export interface SettledOrder {
  orderId: string;
  status: 'LIQUIDADO' | 'NO_ATENDIDO' | 'ANULADO';
  finalTotal?: number;
  deliveryFinal?: number;
  refundToBalance: number;
  refundToMethod: number;
}

export interface ProductSummary {
  productId: string;
  totalQuantity: number;
  tierFrom: number;
  finalPrice: number;
}

export interface CycleSettlement {
  orders: SettledOrder[];
  products: ProductSummary[];
  attendedZones: string[];
  totalToBalance: number;
  totalToMethod: number;
}

// liquidación del ciclo, "te devolvemos" (LQ-01..LQ-08 del equipo)
export function settleCycle(orders: OrderRecord[], cycle: string, zones: Zone[], catalog: Product[]): CycleSettlement {
  const zoneById = new Map(zones.map((zone) => [zone.id, zone]));
  const productById = new Map(catalog.map((product) => [product.id, product]));
  const pending = orders.filter((order) => order.cycleId === cycle && order.status === 'REGISTRADO');
  const settled: SettledOrder[] = [];

  // LQ-01: solo cuentan los pagos verificados; al resto le vuelve el saldo que usó
  const verified = pending.filter((order) => order.paymentStatus === 'VERIFICADO');
  for (const order of pending.filter((item) => item.paymentStatus !== 'VERIFICADO')) {
    settled.push({ orderId: order.id, status: 'ANULADO', refundToBalance: order.paidBalance, refundToMethod: 0 });
  }

  // LQ-02: mínimo por grupo de zonas; si no llega, el Yape vuelve completo (C-06)
  const groupOf = (order: OrderRecord) => zoneById.get(order.zoneId)?.groupId ?? order.zoneId;
  const perGroup = new Map<string, number>();
  for (const order of verified) perGroup.set(groupOf(order), (perGroup.get(groupOf(order)) ?? 0) + 1);
  const attended = verified.filter((order) => (perGroup.get(groupOf(order)) ?? 0) >= MIN_ORDERS_PER_GROUP);
  for (const order of verified.filter((item) => !attended.includes(item))) {
    settled.push({ orderId: order.id, status: 'NO_ATENDIDO', refundToBalance: order.paidBalance, refundToMethod: order.paidExternal });
  }

  // LQ-03 y LQ-04: el tramo sale de lo pedido entre todos los pedidos atendidos
  const totals = new Map<string, number>();
  for (const order of attended) {
    for (const line of order.lines) totals.set(line.productId, (totals.get(line.productId) ?? 0) + line.quantity);
  }
  const products: ProductSummary[] = [];
  const finalPrice = new Map<string, number>();
  for (const [productId, totalQuantity] of totals) {
    const product = productById.get(productId);
    const line = attended.flatMap((order) => order.lines).find((item) => item.productId === productId) as OrderLine;
    const tier = product ? tierFor(product, totalQuantity) : { from: 0, price: line.maxPrice };
    const price = Math.min(tier.price, line.maxPrice); // nunca más de lo que el vecino vio (C-01)
    finalPrice.set(productId, price);
    products.push({ productId, totalQuantity, tierFrom: tier.from, finalPrice: price });
  }

  // LQ-05: la parada de cada zona se reparte entre sus pedidos, con tope de S/ 5
  const perZone = new Map<string, number>();
  for (const order of attended) perZone.set(order.zoneId, (perZone.get(order.zoneId) ?? 0) + 1);

  for (const order of attended) {
    const stopCost = zoneById.get(order.zoneId)?.stopCost ?? MAX_DELIVERY_FEE;
    const delivery = Math.min(stopCost / (perZone.get(order.zoneId) ?? 1), MAX_DELIVERY_FEE);
    const goods = order.lines.reduce((sum, line) => sum + (finalPrice.get(line.productId) ?? line.maxPrice) * line.quantity, 0);
    const finalTotal = floorCents(delivery + goods);
    settled.push({
      orderId: order.id,
      status: 'LIQUIDADO',
      finalTotal,
      deliveryFinal: roundCents(delivery),
      refundToBalance: roundCents(order.total - finalTotal), // C-05: el ahorro vuelve como saldo
      refundToMethod: 0,
    });
  }

  return {
    orders: settled,
    products,
    attendedZones: [...perZone.keys()],
    totalToBalance: roundCents(settled.filter((item) => item.status === 'LIQUIDADO').reduce((sum, item) => sum + item.refundToBalance, 0)),
    totalToMethod: roundCents(settled.reduce((sum, item) => sum + item.refundToMethod, 0)),
  };
}

export function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

export function validateAuthInput(input: { mode: 'login' | 'register'; name?: string; phone?: string; email: string; password: string }): string | null {
  if (input.mode === 'register' && !input.name?.trim()) return 'Cuéntanos cómo te llamas para crear tu cuenta.';
  if (input.mode === 'register' && !/^9\d{8}$/.test((input.phone || '').replace(/\s/g, ''))) return 'Ingresa un celular peruano de 9 dígitos que empiece con 9.';
  if (!validateEmail(input.email)) return 'Revisa tu correo electrónico.';
  if (input.password.length < 8) return 'Tu contraseña debe tener al menos 8 caracteres.';
  return null;
}

export function createOrderCode(sequence = Date.now()): string {
  return `YP-${String(sequence).slice(-4).padStart(4, '0')}`;
}

import type { OrderSelection } from '../types';

export const MIN_SUBTOTAL = 50;
export const FREE_DELIVERY_FROM = 120;
export const DELIVERY_FEE = 7.9;
export const SUPPORTED_DISTRICTS = ['Lince', 'Jesús María', 'La Victoria'] as const;

export function calculateDeliveryFee(subtotal: number): number {
  return subtotal >= FREE_DELIVERY_FROM ? 0 : DELIVERY_FEE;
}

export function canCheckout(subtotal: number): boolean {
  return subtotal >= MIN_SUBTOTAL;
}

export function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

export function validateAuthInput(input: { mode: 'login' | 'register'; name?: string; phone?: string; email: string; password: string }): string | null {
  if (input.mode === 'register' && !input.name?.trim()) return 'Cuéntanos cómo te llamas para crear tu cuenta.';
  if (input.mode === 'register' && !/^\d{9}$/.test((input.phone || '').replace(/\s/g, ''))) return 'Ingresa un celular peruano de 9 dígitos.';
  if (!validateEmail(input.email)) return 'Revisa tu correo electrónico.';
  if (input.password.length < 8) return 'Tu contraseña debe tener al menos 8 caracteres.';
  return null;
}

export function validateOrderSelection(selection: OrderSelection, subtotal: number): string | null {
  if (!canCheckout(subtotal)) return `Te faltan S/ ${(MIN_SUBTOTAL - subtotal).toFixed(2)} para llegar al mínimo.`;
  if (!SUPPORTED_DISTRICTS.includes(selection.district as (typeof SUPPORTED_DISTRICTS)[number])) return 'Selecciona un distrito dentro de la cobertura piloto.';
  if (!selection.addressLine.trim()) return 'Ingresa una dirección de entrega.';
  return null;
}

export function createOrderCode(sequence = Date.now()): string {
  return `YP-${String(sequence).slice(-4).padStart(4, '0')}`;
}

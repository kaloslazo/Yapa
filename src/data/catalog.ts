import type { DeliveryWindow, PaymentMethod, Product, Zone } from '../types';

// precios de ejemplo (S-12): el primero es el máximo; los tramos bajan si entre todos se pide más
export const products: Product[] = [
  {
    id: 'arroz-extra',
    name: 'Arroz extra',
    category: 'Despensa',
    price: 4.8,
    unit: 'kg',
    detail: 'Grano largo, calidad mayorista',
    art: 'rice',
    image: '/images/products/arroz-extra.png',
    stock: 300,
    tiers: [{ from: 0, price: 4.8 }, { from: 100, price: 4.5 }, { from: 250, price: 4.3 }],
  },
  {
    id: 'aceite-vegetal',
    name: 'Aceite vegetal',
    category: 'Despensa',
    price: 8.9,
    unit: 'L',
    detail: 'Botella familiar de 1 litro',
    art: 'oil',
    image: '/images/products/aceite-vegetal.png',
    stock: 120,
    tiers: [{ from: 0, price: 8.9 }, { from: 24, price: 8.4 }],
  },
  {
    id: 'platano-seda',
    name: 'Plátano de seda',
    category: 'Frutas',
    price: 3.9,
    unit: 'kg',
    detail: 'Dulce y listo para la semana',
    art: 'banana',
    image: '/images/products/platano-seda.png',
    stock: 150,
    tiers: [{ from: 0, price: 3.9 }, { from: 60, price: 3.5 }],
  },
  {
    id: 'tomate-italiano',
    name: 'Tomate italiano',
    category: 'Verduras',
    price: 5.6,
    unit: 'kg',
    detail: 'Cosecha seleccionada del día',
    art: 'tomato',
    image: '/images/products/tomate-italiano.png',
    stock: 200,
    tiers: [{ from: 0, price: 5.6 }, { from: 80, price: 4.9 }],
  },
  {
    id: 'papa-amarilla',
    name: 'Papa amarilla',
    category: 'Verduras',
    price: 4.2,
    unit: 'kg',
    detail: 'Textura cremosa para guisos',
    art: 'potato',
    image: '/images/products/papa-amarilla.png',
    stock: 400,
    tiers: [{ from: 0, price: 4.2 }, { from: 100, price: 3.9 }, { from: 250, price: 3.7 }],
  },
  {
    id: 'leche-pack',
    name: 'Leche evaporada',
    category: 'Lácteos',
    price: 21.6,
    unit: 'pack x 6',
    detail: 'Seis latas para la despensa',
    art: 'milk',
    image: '/images/products/leche-pack.png',
    stock: 60,
    tiers: [{ from: 0, price: 21.6 }, { from: 12, price: 20.4 }],
  },
];

export const deliveryWindows: DeliveryWindow[] = [
  { code: 'SAT_09_12', label: '09:00 – 12:00' },
  { code: 'SAT_12_15', label: '12:00 – 15:00' },
  { code: 'SAT_15_18', label: '15:00 – 18:00' },
];

// zonas del piloto: Yapa asigna la ventana a cada zona porque recibe la portería (S-10)
export const zones: Zone[] = [
  { id: 'Z-LINCE-01', name: 'Edificio Los Álamos', district: 'Lince', groupId: 'G-LINCE', stopCost: 40, deliveryWindow: 'SAT_09_12', active: true, coordinates: { lat: -12.086, lng: -77.034 } },
  { id: 'Z-LINCE-02', name: 'Condominio Las Palmeras', district: 'Lince', groupId: 'G-LINCE', stopCost: 40, deliveryWindow: 'SAT_09_12', active: true, coordinates: { lat: -12.084, lng: -77.0335 } },
  { id: 'Z-JM-01', name: 'Residencial San Felipe', district: 'Jesús María', groupId: 'G-JM', stopCost: 40, deliveryWindow: 'SAT_12_15', active: true, coordinates: { lat: -12.0765, lng: -77.047 } },
  { id: 'Z-LV-01', name: 'Edificio Balconcillo', district: 'La Victoria', groupId: 'G-LV', stopCost: 40, deliveryWindow: 'SAT_15_18', active: false, coordinates: { lat: -12.069, lng: -77.023 } },
];

export const DEFAULT_ZONE_ID = 'Z-LINCE-01';

export function zoneById(id: string | undefined): Zone | undefined {
  return zones.find((zone) => zone.id === id);
}

export function windowLabel(code: string | undefined): string {
  return deliveryWindows.find((window) => window.code === code)?.label ?? '';
}

export const paymentMethods: PaymentMethod[] = [
  { value: 'YAPE', label: 'Yape' },
  { value: 'PLIN', label: 'Plin' },
];

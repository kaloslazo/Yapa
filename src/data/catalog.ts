import type { DeliveryWindow, PaymentMethod, Product } from '../types';

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
    stock: 28,
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
    stock: 16,
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
    stock: 22,
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
    stock: 18,
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
    stock: 31,
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
    stock: 12,
  },
];

export const deliveryWindows: DeliveryWindow[] = [
  { code: 'SAT_09_12', label: '09:00 – 12:00', capacity: '8 cupos disponibles' },
  { code: 'SAT_12_15', label: '12:00 – 15:00', capacity: '12 cupos disponibles' },
  { code: 'SAT_15_18', label: '15:00 – 18:00', capacity: '5 cupos disponibles' },
];

export const paymentMethods: PaymentMethod[] = [
  { value: 'TRANSFERENCIA', label: 'Transferencia bancaria', note: 'Verificación hasta el jueves 12:00' },
  { value: 'BILLETERA_DIGITAL', label: 'Billetera digital', note: 'Yape o Plin' },
  { value: 'CONTRAENTREGA', label: 'Contraentrega', note: 'Paga al recibir tu canasta' },
];

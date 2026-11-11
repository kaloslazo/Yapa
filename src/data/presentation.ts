import type { ProductArtName } from '../types';

// cómo se ve cada producto del catálogo del piloto (S-169); el precio y las reglas vienen de la API
interface Look {
  detail: string;
  art: ProductArtName;
  image?: string;
  jug?: [string, string]; // galones sin foto: color del líquido y de la tapa
  group: GroupId; // grupo para mostrar en la tienda; en el motor siguen siendo FRESCOS o LIMPIEZA
  tint: string; // pastel detrás de la foto
  emoji: string;
}

export type GroupId = 'tuberculos' | 'verduras' | 'limpieza';

// grupos de la tienda (Explorar); «ofertas» se arma con el ahorro frente al súper
export const groups: Array<{ id: GroupId | 'ofertas'; name: string; tint: string }> = [
  { id: 'tuberculos', name: 'Tubérculos', tint: '#fff4c7' },
  { id: 'verduras', name: 'Verduras y frutas', tint: '#efe7fb' },
  { id: 'limpieza', name: 'Limpieza', tint: '#e2f0fb' },
  { id: 'ofertas', name: 'Ofertas', tint: '#ffe9dc' },
];

const looks: Record<string, Look> = {
  'PAPA-AMARILLA': { detail: 'Cremosa, ideal para causa y puré', art: 'potato', image: '/images/products/papa-amarilla.webp', group: 'tuberculos', tint: '#fff4c7', emoji: '🥔' },
  'PAPA-BLANCA': { detail: 'Rendidora para el día a día', art: 'potato', image: '/images/products/papa-blanca.webp', group: 'tuberculos', tint: '#f6efe4', emoji: '🥔' },
  CAMOTE: { detail: 'Amarillo y dulce', art: 'oil', image: '/images/products/camote.webp', group: 'tuberculos', tint: '#ffe9dc', emoji: '🍠' },
  'CEBOLLA-ROJA': { detail: 'Para el aderezo y el sarza', art: 'tomato', image: '/images/products/cebolla-roja.webp', group: 'verduras', tint: '#efe7fb', emoji: '🧅' },
  AJO: { detail: 'Criollo, por cuartos de kilo', art: 'rice', image: '/images/products/ajo.webp', group: 'verduras', tint: '#eef1ec', emoji: '🧄' },
  LIMON: { detail: 'Jugoso, para el ceviche', art: 'banana', image: '/images/products/limon.webp', group: 'verduras', tint: '#e3f6ec', emoji: '🍋' },
  ZANAHORIA: { detail: 'Fresca, de mercado mayorista', art: 'oil', image: '/images/products/zanahoria.webp', group: 'verduras', tint: '#ffe5d0', emoji: '🥕' },
  'PLATANO-SEDA': { detail: 'Dulce y listo para la semana', art: 'banana', image: '/images/products/platano-seda.webp', group: 'verduras', tint: '#fff4c7', emoji: '🍌' },
  'LIMPIATODO-GALON': { detail: 'Sapolio, aroma lavanda', art: 'milk', image: '/images/products/limpiatodo.webp', group: 'limpieza', tint: '#efe7fb', emoji: '🧴' },
  'LAVAVAJILLAS-GALON': { detail: 'Ayudín, limón y sábila', art: 'milk', image: '/images/products/lavavajillas.webp', group: 'limpieza', tint: '#e3f6ec', emoji: '🧽' },
  'DETERGENTE-LIQUIDO-GALON': { detail: 'Bolívar Cuidado Total, para la ropa', art: 'milk', image: '/images/products/detergente-liquido.webp', group: 'limpieza', tint: '#e2f0fb', emoji: '🫧' },
  'LEJIA-GALON': { detail: 'Sapolio, para desinfectar', art: 'milk', image: '/images/products/lejia.webp', group: 'limpieza', tint: '#eef2f5', emoji: '🧪' },
};

export const categoryNames: Record<string, string> = { FRESCOS: 'Frescos', LIMPIEZA: 'Limpieza' };

export function lookFor(id: string, category: string): Look {
  const cleaning = category === 'LIMPIEZA';
  return looks[id] ?? { detail: cleaning ? 'Formato grande' : 'Fresco de la semana', art: cleaning ? 'milk' : 'potato', group: cleaning ? 'limpieza' : 'verduras', tint: cleaning ? '#e2f0fb' : '#eef1ec', emoji: cleaning ? '🧴' : '🧺' };
}

export const deliveryWindows = ['09:00 – 12:00', '12:00 – 15:00', '15:00 – 18:00'];

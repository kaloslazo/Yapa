import type { ProductArtName } from '../types';

// cómo se ve cada producto del catálogo del piloto (S-169); el precio y las reglas vienen de la API
interface Look {
  detail: string;
  art: ProductArtName;
  image?: string;
  jug?: [string, string]; // galones sin foto: color del líquido y de la tapa
  emoji: string;
}

const looks: Record<string, Look> = {
  'PAPA-AMARILLA': { detail: 'Cremosa, ideal para causa y puré', art: 'potato', image: '/images/products/papa-amarilla.webp', emoji: '🥔' },
  'PAPA-BLANCA': { detail: 'Rendidora para el día a día', art: 'potato', image: '/images/products/papa-blanca.webp', emoji: '🥔' },
  'CEBOLLA-ROJA': { detail: 'Para el aderezo y el sarza', art: 'tomato', image: '/images/products/cebolla-roja.webp', emoji: '🧅' },
  AJO: { detail: 'Criollo, por cuartos de kilo', art: 'rice', image: '/images/products/ajo.webp', emoji: '🧄' },
  LIMON: { detail: 'Jugoso, para el ceviche', art: 'banana', image: '/images/products/limon.webp', emoji: '🍋' },
  CAMOTE: { detail: 'Amarillo y dulce', art: 'oil', image: '/images/products/camote.webp', emoji: '🍠' },
  ZANAHORIA: { detail: 'Fresca, de mercado mayorista', art: 'oil', image: '/images/products/zanahoria.webp', emoji: '🥕' },
  'PLATANO-SEDA': { detail: 'Dulce y listo para la semana', art: 'banana', image: '/images/products/platano-seda.webp', emoji: '🍌' },
  'LIMPIATODO-GALON': { detail: 'Galón de 3.8 L, rinde el mes', art: 'milk', jug: ['#c3b3ee', '#6b4fc8'], emoji: '🧴' },
  'LAVAVAJILLAS-GALON': { detail: 'Galón para la cocina', art: 'milk', jug: ['#a8e3ae', '#2f9a48'], emoji: '🧽' },
  'DETERGENTE-LIQUIDO-GALON': { detail: 'Galón para la ropa', art: 'milk', jug: ['#a6cdf3', '#2369b8'], emoji: '🫧' },
  'LEJIA-GALON': { detail: 'Galón para desinfectar', art: 'milk', jug: ['#f4f4ee', '#2b72c9'], emoji: '🧪' },
};

export const categoryNames: Record<string, string> = { FRESCOS: 'Frescos', LIMPIEZA: 'Limpieza' };

export function lookFor(id: string, category: string): Look {
  return looks[id] ?? { detail: category === 'LIMPIEZA' ? 'Formato grande' : 'Fresco de la semana', art: category === 'LIMPIEZA' ? 'milk' : 'potato', emoji: category === 'LIMPIEZA' ? '🧴' : '🧺' };
}

export const deliveryWindows = ['09:00 – 12:00', '12:00 – 15:00', '15:00 – 18:00'];

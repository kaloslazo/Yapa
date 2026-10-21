import type { ProductArtName } from '../types';

// cómo se ve cada producto del catálogo del piloto (S-169); el precio y las reglas vienen de la API
interface Look {
  detail: string;
  art: ProductArtName;
  image?: string;
  emoji: string;
}

const looks: Record<string, Look> = {
  'PAPA-AMARILLA': { detail: 'Cremosa, ideal para causa y puré', art: 'potato', image: '/images/products/papa-amarilla.webp', emoji: '🥔' },
  'PAPA-BLANCA': { detail: 'Rendidora para el día a día', art: 'potato', emoji: '🥔' },
  'CEBOLLA-ROJA': { detail: 'Para el aderezo y el sarza', art: 'tomato', emoji: '🧅' },
  AJO: { detail: 'Criollo, por cuartos de kilo', art: 'rice', emoji: '🧄' },
  LIMON: { detail: 'Jugoso, para el ceviche', art: 'banana', emoji: '🍋' },
  CAMOTE: { detail: 'Amarillo y dulce', art: 'oil', emoji: '🍠' },
  ZANAHORIA: { detail: 'Fresca, de mercado mayorista', art: 'oil', emoji: '🥕' },
  'PLATANO-SEDA': { detail: 'Dulce y listo para la semana', art: 'banana', image: '/images/products/platano-seda.webp', emoji: '🍌' },
  'LIMPIATODO-GALON': { detail: 'Galón de 3.8 L, rinde el mes', art: 'milk', emoji: '🧴' },
  'LAVAVAJILLAS-GALON': { detail: 'Galón para la cocina', art: 'milk', emoji: '🧽' },
  'DETERGENTE-LIQUIDO-GALON': { detail: 'Galón para la ropa', art: 'milk', emoji: '🫧' },
  'LEJIA-GALON': { detail: 'Galón para desinfectar', art: 'milk', emoji: '🧪' },
};

export const categoryNames: Record<string, string> = { FRESCOS: 'Frescos', LIMPIEZA: 'Limpieza' };

export function lookFor(id: string, category: string): Look {
  return looks[id] ?? { detail: category === 'LIMPIEZA' ? 'Formato grande' : 'Fresco de la semana', art: category === 'LIMPIEZA' ? 'milk' : 'potato', emoji: category === 'LIMPIEZA' ? '🧴' : '🧺' };
}

export const deliveryWindows = ['09:00 – 12:00', '12:00 – 15:00', '15:00 – 18:00'];

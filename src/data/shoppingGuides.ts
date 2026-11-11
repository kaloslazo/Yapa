export interface ShoppingGuide {
  id: string;
  title: string;
  intro: string;
  image: string;
  tint: string;
  tips: string[];
}

// guías cortas para el final de Explorar: explican sin fijar precios, plazos ni políticas nuevas
export const shoppingGuides: ShoppingGuide[] = [
  {
    id: 'precio', title: 'Lo que pagas y lo que puede volver',
    intro: 'El precio de tu canasta y el ahorro de comprar en grupo son dos cosas distintas.',
    image: '/images/products/ajo.webp', tint: '#e3f6ec',
    tips: ['El total de tu canasta es lo máximo que vas a pagar.', 'Si entre todos conseguimos un precio más bajo, el 75 % de esa baja vuelve a tu saldo; el 25 % sostiene la operación de Yapa.', 'Ese ahorro se calcula después de la entrega. Antes es solo una estimación.'],
  },
  {
    id: 'grupo', title: 'Qué significa llegar al mínimo del grupo',
    intro: 'No basta con tener vecinos inscritos: cuentan los pedidos con pago verificado.',
    image: '/images/products/cebolla-roja.webp', tint: '#efe7fb',
    tips: ['El grupo necesita al menos 8 pedidos con pago verificado para que compremos.', 'Si ya entraste, en Inicio ves cuántos pedidos lleva tu edificio.', 'Si no se llega, te devolvemos el pago a tu Yape o Plin. El pedido no pasa solo a la semana siguiente.'],
  },
  {
    id: 'recepcion', title: 'Recoge tu pedido sin confusiones',
    intro: 'Ten a mano tu número de pedido y revisa las bolsas que te corresponden.',
    image: '/images/products/camote.webp', tint: '#ffe9dc',
    tips: ['El sábado dejamos tu pedido en la portería de tu edificio. En Mis pedidos ves en qué va.', 'Al recogerlo, revisa el número de pedido y cuántas bolsas son. No te lleves una bolsa de otro vecino.', 'Si algo no cuadra con tu pedido, reclámalo desde Mis pedidos con una foto.'],
  },
];

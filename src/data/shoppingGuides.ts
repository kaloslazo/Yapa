export interface ShoppingGuide {
  id: string;
  category: string;
  title: string;
  intro: string;
  image: string;
  tint: string;
  tips: string[];
}

// Contenido editorial propio: orienta sin fijar precios, disponibilidad ni políticas nuevas.
export const shoppingGuides: ShoppingGuide[] = [
  {
    id: 'planifica', category: 'Tu semana', title: 'Una canasta que sí vas a usar',
    intro: 'Antes de agregar productos, mira qué tienes en casa y qué piensas preparar.',
    image: '/images/products/zanahoria.webp', tint: '#ffe9dc',
    tips: ['Haz una lista corta de comidas y revisa lo que ya tienes. Evitas pedir dos veces lo mismo.', 'Busca ingredientes que te sirvan para más de una preparación, como papa, zanahoria o cebolla.', 'Ajusta las cantidades a quienes comen en casa. Comprar más no ayuda si al final no lo usas.'],
  },
  {
    id: 'precio', category: 'Ahorro claro', title: 'Lo que pagas y lo que puede volver',
    intro: 'El precio máximo y el ahorro por compra grupal son dos cosas distintas.',
    image: '/images/products/ajo.webp', tint: '#e3f6ec',
    tips: ['Revisa el total de tu canasta antes de pagar. Ese es el máximo mostrado para tu pedido.', 'Si la compra conjunta consigue una baja, el 75 % de esa baja vuelve a tu saldo; el 25 % sostiene la operación de Yapa.', 'El resultado se calcula después de la entrega. No cuentes una estimación como dinero que ya tienes disponible.'],
  },
  {
    id: 'unidades', category: 'Al elegir', title: 'Un kilo no es lo mismo que una unidad',
    intro: 'Fíjate en la medida del producto para comparar y pedir la cantidad correcta.',
    image: '/images/products/papa-amarilla.webp', tint: '#fff4c7',
    tips: ['Mira si el precio corresponde a un kilo, una unidad o una presentación específica.', 'Para comparar dos opciones, usa la misma medida y considera el contenido del envase.', 'Comprueba la cantidad final en la canasta. El catálogo indica los pasos de cantidad disponibles para cada producto.'],
  },
  {
    id: 'grupo', category: 'Entre vecinos', title: 'Qué significa llegar al mínimo del grupo',
    intro: 'No basta con tener vecinos inscritos: cuentan los pedidos con pago verificado.',
    image: '/images/products/cebolla-roja.webp', tint: '#efe7fb',
    tips: ['El grupo necesita al menos ocho pedidos con pago verificado para activar la compra.', 'En Inicio puedes revisar el avance de tu grupo si ya ingresaste y tienes una zona asignada.', 'Si no se alcanza el mínimo, corresponde devolver el pago a Yape o Plin. No asumas que tu pedido pasará automáticamente a la siguiente semana.'],
  },
  {
    id: 'recepcion', category: 'Al recibir', title: 'Recoge tu pedido sin confusiones',
    intro: 'Ten a mano tu número de pedido y revisa las bolsas que te corresponden.',
    image: '/images/products/camote.webp', tint: '#ffe9dc',
    tips: ['Consulta Mis pedidos para revisar el seguimiento. La entrega se realiza el sábado en el punto de recepción de tu zona.', 'Al recoger, comprueba el número de pedido y la cantidad de bolsas. Recibir en portería y retirar tu compra son momentos distintos.', 'Compara lo recibido con tu pedido y avisa si hay diferencias. Evita llevarte una bolsa que corresponde a otro vecino.'],
  },
  {
    id: 'ayuda', category: 'Si algo falla', title: 'Cómo explicar un problema con tu compra',
    intro: 'Un reporte claro ayuda a que atención entienda qué ocurrió.',
    image: '/images/products/limon.webp', tint: '#e2f0fb',
    tips: ['Abre el pedido correspondiente e identifica el producto y la cantidad con el problema.', 'Describe si faltó, llegó distinto o estaba dañado. Adjunta una foto cuando el formulario la solicite.', 'La solución depende de la revisión del caso. El reporte no significa que ya se aprobó una reposición o devolución.'],
  },
];

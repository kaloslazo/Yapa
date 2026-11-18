export type FaqTopicName = 'Pagos' | 'Entregas' | 'Pedidos' | 'Cuenta';

// cada pregunta trae su tema y las palabras extra con que la encuentra el buscador del chat (iteración 73)
export interface Faq { q: string; a: string; topic: FaqTopicName; keywords: string }

export const faqs: Faq[] = [
  { q: '¿Hasta cuándo puedo pedir?', a: 'Hasta el miércoles a las 8 p. m., hora de Lima, con el pago hecho. A esa hora se cierra la semana.', topic: 'Pedidos', keywords: 'horario cierre pedir comprar' },
  { q: '¿Cómo pago mi pedido?', a: 'Con Yape o Plin, por adelantado. Al confirmar te damos un código: escríbelo en el mensaje del pago y con él verificamos que pagaste. No hay pago contra entrega.', topic: 'Pagos', keywords: 'pago pagar pague yape plin comprobante' },
  { q: '¿Cuánto voy a pagar?', a: 'Lo que ves en tu canasta es el máximo. Si entre todos pedimos más y el precio baja, el 75 % de esa baja vuelve a tu saldo después de la entrega; el 25 % sostiene la operación de Yapa.', topic: 'Pagos', keywords: 'precio costo ahorro descuento' },
  { q: '¿Qué pasa si mi grupo no llega al mínimo?', a: 'Cada grupo necesita 8 pedidos. Si no llegamos, te devolvemos el 100 % a tu Yape o Plin.', topic: 'Pedidos', keywords: 'grupo minimo vecinos ocho' },
  { q: '¿Dónde y cuándo entregan?', a: 'Los sábados, en la portería de tu edificio, en Lince y Jesús María. La Victoria abre pronto.', topic: 'Entregas', keywords: 'entrega reparto llega direccion sabado' },
  { q: '¿Cómo sé que llegó mi pedido?', a: 'Cada entrega queda registrada con foto. Si algo faltó, lo reclamas desde Mis pedidos.', topic: 'Entregas', keywords: 'entrega llego compra pedido demora pendiente' },
  { q: '¿Puedo cancelar?', a: 'Sí, hasta el miércoles a las 8 p. m. desde Mis pedidos, y te devolvemos todo.', topic: 'Pedidos', keywords: 'cancelar anulacion cancelar compra' },
  { q: '¿Cómo me registro?', a: 'Con el enlace de invitación de un vecino o del admin de tu edificio. Usas tu correo o tu cuenta de Google.', topic: 'Cuenta', keywords: 'registro ingresar acceso cuenta invitacion' },
  { q: '¿Qué hago si falta un producto o llegó dañado?', a: 'Reclámalo desde Mis pedidos con una foto, hasta 24 h después de la entrega. El equipo lo revisa antes de devolverte algo.', topic: 'Entregas', keywords: 'reclamo faltante danado malogrado producto falta' },
  { q: '¿Qué hago con mi saldo?', a: 'Lo usas en tu próxima compra o lo pides de vuelta a tu Yape o Plin.', topic: 'Pagos', keywords: 'saldo devolver devolucion reembolso' },
];

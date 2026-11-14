import { faqs } from '../data/faqs';

export const FAQ_TOPICS = ['Todas', 'Pagos', 'Entregas', 'Pedidos', 'Cuenta'] as const;
export type FaqTopic = typeof FAQ_TOPICS[number];
const topics: FaqTopic[] = ['Pedidos', 'Pagos', 'Pagos', 'Pedidos', 'Entregas', 'Entregas', 'Pedidos', 'Cuenta', 'Entregas', 'Pagos'];
const aliases = ['horario cierre pedir comprar', 'pago pagar pague yape plin comprobante', 'precio costo ahorro descuento', 'grupo minimo vecinos ocho', 'entrega reparto llega direccion sabado', 'entrega llego compra pedido demora pendiente', 'cancelar anulacion cancelar compra', 'registro ingresar acceso cuenta invitacion', 'reclamo faltante danado malogrado producto falta', 'saldo devolver devolucion reembolso'];
const synonyms: Record<string, string> = { pague: 'pago', pagar: 'pago', pagado: 'pago', pagos: 'pago', entregan: 'entrega', entregas: 'entrega', llego: 'entrega', llegar: 'entrega', llegara: 'entrega', lleguen: 'entrega', danados: 'danado', malogrado: 'danado', faltan: 'faltante', devolver: 'devolucion', reembolso: 'devolucion', registrarme: 'registro', registro: 'registro', comprar: 'pedir', compras: 'compra' };
const stopwords = new Set('a al de del el la las los un una unos unas que como cuando donde por para con mi mis me se si no y o es esta este puedo quiero tengo hacer'.split(' '));
export function normalizeFaq(text: string): string {
  return text.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
}
function tokens(text: string): string[] {
  return [...new Set(normalizeFaq(text).split(' ').filter(t => t && !stopwords.has(t)).map(t => synonyms[t] ?? t))];
}
export function searchFaq(query: string, topic: FaqTopic = 'Todas') {
  const terms = tokens(query.slice(0, 300));
  return faqs.map((faq, id) => {
    const question = tokens(faq.q), answer = tokens(faq.a), extra = tokens(aliases[id]);
    const score = terms.reduce((n, t) => n + (question.includes(t) ? 4 : 0) + (extra.includes(t) ? 3 : 0) + (answer.includes(t) ? 1 : 0), 0);
    return { ...faq, id, topic: topics[id], score };
  }).filter(f => (topic === 'Todas' || f.topic === topic) && (!query.trim() || (terms.length > 0 && f.score > 0)))
    .sort((a, b) => b.score - a.score || a.id - b.id);
}

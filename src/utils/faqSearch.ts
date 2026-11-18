import { faqs } from '../data/faqs';

export const FAQ_TOPICS = ['Todas', 'Pagos', 'Entregas', 'Pedidos', 'Cuenta'] as const;
export type FaqTopic = typeof FAQ_TOPICS[number];

const MAX_QUERY = 300;
// peso de cada coincidencia: en la pregunta pesa más que en las palabras extra, y estas más que en la respuesta
const IN_QUESTION = 4;
const IN_KEYWORDS = 3;
const IN_ANSWER = 1;
const synonyms: Record<string, string> = {
  pague: 'pago', pagar: 'pago', pagado: 'pago', pagos: 'pago', entregan: 'entrega', entregas: 'entrega', llego: 'entrega',
  llegar: 'entrega', llegara: 'entrega', lleguen: 'entrega', danados: 'danado', malogrado: 'danado', faltan: 'faltante',
  devolver: 'devolucion', reembolso: 'devolucion', registrarme: 'registro', registro: 'registro', comprar: 'pedir', compras: 'compra',
};
const stopwords = new Set('a al de del el la las los un una unos unas que como cuando donde por para con mi mis me se si no y o es esta este puedo quiero tengo hacer'.split(' '));

export function normalizeFaq(text: string): string {
  return text.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, ' ').trim();
}

function tokens(text: string): string[] {
  return [...new Set(normalizeFaq(text).split(' ').filter((t) => t && !stopwords.has(t)).map((t) => synonyms[t] ?? t))];
}

// iteración 73 (CH73-1): busca sin IA en las preguntas frecuentes; las de más coincidencias primero
export function searchFaq(query: string, topic: FaqTopic = 'Todas') {
  const terms = tokens(query.slice(0, MAX_QUERY));
  return faqs.map((faq, id) => {
    const question = tokens(faq.q);
    const answer = tokens(faq.a);
    const extra = tokens(faq.keywords);
    const score = terms.reduce((n, t) => n
      + (question.includes(t) ? IN_QUESTION : 0) + (extra.includes(t) ? IN_KEYWORDS : 0) + (answer.includes(t) ? IN_ANSWER : 0), 0);
    return { ...faq, id, score };
  })
    .filter((f) => (topic === 'Todas' || f.topic === topic) && (!query.trim() || (terms.length > 0 && f.score > 0)))
    .sort((a, b) => b.score - a.score || a.id - b.id);
}

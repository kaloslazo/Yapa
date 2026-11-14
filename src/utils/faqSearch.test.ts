import { describe, expect, it } from 'vitest';
import { searchFaq } from './faqSearch';
describe('búsqueda de ayuda', () => {
  it('reutiliza las diez preguntas y filtra por tema', () => { expect(searchFaq('')).toHaveLength(10); expect(searchFaq('', 'Entregas')).toHaveLength(3); });
  it('entiende tildes y variantes de pago', () => { expect(searchFaq('PAGUÉ')[0].q).toBe('¿Cómo pago mi pedido?'); });
  it('ofrece entregas para una compra que no llegó', () => { expect(searchFaq('no llegó mi compra').some(f => f.topic === 'Entregas')).toBe(true); });
  it('no fabrica respuesta para algo desconocido o palabras vacías', () => { expect(searchFaq('astronauta galaxia')).toHaveLength(0); expect(searchFaq('como que')).toHaveLength(0); });
  it('respeta el tema aunque una consulta coincida con otro', () => { expect(searchFaq('pagué', 'Cuenta')).toHaveLength(0); });
});

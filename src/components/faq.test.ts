import { describe, expect, it } from 'vitest';
import { faqs } from './EditorialSections';

// iteración 57, S-302: la portada dice cuánto del ahorro vuelve al vecino y cuánto se queda Yapa (Ley 29571)
describe('preguntas frecuentes', () => {
  it('"¿Cuánto voy a pagar?" explica el 75 % y el 25 %', () => {
    const answer = faqs.find((f) => f.q === '¿Cuánto voy a pagar?')?.a ?? '';
    expect(answer).toContain('75 %');
    expect(answer).toContain('25 %');
  });
});

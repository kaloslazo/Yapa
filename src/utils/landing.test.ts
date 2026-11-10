import { describe, expect, it } from 'vitest';
import { bestDeals, closeCountdown } from './landing';

// rediseño de la portada: cuánto falta para el cierre del miércoles 20:00 (hora de Lima, S-02)
describe('cuenta regresiva al cierre', () => {
  it('días y horas mientras falta más de un día', () => {
    expect(closeCountdown(new Date('2026-11-09T15:00:00-05:00'))).toEqual({ open: true, text: 'Cierra en 2 d 5 h' });
  });
  it('horas y minutos el último día', () => {
    expect(closeCountdown(new Date('2026-11-11T17:35:00-05:00'))).toEqual({ open: true, text: 'Cierra en 2 h 25 min' });
  });
  it('después del cierre dice cuándo vuelve a abrir', () => {
    expect(closeCountdown(new Date('2026-11-11T20:00:00-05:00'))).toEqual({ open: false, text: 'Abre el lunes' });
    expect(closeCountdown(new Date('2026-11-14T10:00:00-05:00'))).toEqual({ open: false, text: 'Abre el lunes' });
  });
});

describe('pizarra de la semana', () => {
  const p = (id: string, saving: number | null) => ({ id, supermarketSaving: saving, supermarket: saving === null ? null : { price: 1 } });
  it('las que más ahorran frente al supermercado, sin las que no tienen referencia', () => {
    expect(bestDeals([p('a', 20), p('b', null), p('c', 60), p('d', 45)], 2).map((x) => x.id)).toEqual(['c', 'd']);
  });
});

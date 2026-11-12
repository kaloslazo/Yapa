import { describe, expect, it } from 'vitest';
import { shortDate, weekLabel, weekRangeLabel } from './week';

describe('PA-01 · fechas para Armado', () => {
  it('muestra lunes, domingo y año incluso al cruzar de año', () => {
    expect(weekRangeLabel('2026-W40')).toBe('28 sep – 4 oct 2026');
    expect(weekRangeLabel('2026-W01')).toBe('29 dic 2025 – 4 ene 2026');
    expect(weekRangeLabel('sin semana')).toBe('sin semana');
  });
});

describe('UX-02 · la semana en palabras para el vecino', () => {
  it('dice el lunes de la semana', () => {
    expect(weekLabel('2026-W40')).toBe('semana del 28 sep');
    expect(weekLabel('2026-W43')).toBe('semana del 19 oct');
  });

  it('cruza el año como el calendario ISO', () => {
    expect(weekLabel('2026-W01')).toBe('semana del 29 dic');
    expect(weekLabel('2027-W01')).toBe('semana del 4 ene');
  });

  it('deja el texto como venía si no es una semana', () => {
    expect(weekLabel('')).toBe('');
    expect(weekLabel('W40')).toBe('W40');
  });
});

describe('UX-03 · fecha corta del precio de referencia', () => {
  it('día y mes', () => {
    expect(shortDate('2026-09-24')).toBe('24 sep');
    expect(shortDate('no-es-fecha')).toBe('');
  });
});

import { describe, expect, it } from 'vitest';
import { unseenReceptionEvents } from './receptionUpdates';

describe('PO-02 · avisos de portería', () => {
  const initial = { ciclo: '2026-W39', zona: { id: 'Z-LINCE-01' }, hitos: [{ estado: 'listo', hora: '2026-09-25T10:00:00-05:00' }] };
  it('no avisa por la primera carga ni al cambiar de semana', () => {
    expect(unseenReceptionEvents(null, initial)).toEqual([]);
    expect(unseenReceptionEvents(initial, { ...initial, ciclo: '2026-W40' })).toEqual([]);
  });
  it('avisa todos los hitos nuevos entre consultas sin repetir los anteriores', () => {
    const next = { ...initial, hitos: [...initial.hitos, { estado: 'en_camino', hora: '2026-09-26T08:00:00-05:00' }, { estado: 'entregada', hora: '2026-09-26T10:00:00-05:00' }] };
    expect(unseenReceptionEvents(initial, next).map(e => e.estado)).toEqual(['en_camino', 'entregada']);
    expect(unseenReceptionEvents(next, next)).toEqual([]);
  });
  it('avisa cuando aparecen pedidos para preparar aunque todavía no tengan bolsas ni hitos', () => {
    const before = { ...initial, seguimiento: 'sin_pedidos', hitos: [] };
    const after = { ...before, seguimiento: 'preparando' };
    expect(unseenReceptionEvents(before, after).map(e => e.estado)).toEqual(['preparando']);
  });
});

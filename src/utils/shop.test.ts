import { describe, expect, it } from 'vitest';
import { applyChip, deliveryDay, dropFill, inGroup, nearDrop } from './shop';

// estructura nueva de la tienda (fase 1): secciones del inicio, grupos, chips y día de entrega
const p = (id: string, group: string, ordered: number, saving: number | null, tiers = [{ from: 0, price: 2 }, { from: 10, price: 1 }]) => ({
  id, group, ordered, tiers, nextTier: tiers.find((t) => t.from > ordered) ?? null, supermarketSaving: saving, supermarket: saving === null ? null : { price: 3 },
});
const list = [p('a', 'tuberculos', 2, 30), p('b', 'verduras', 9, null), p('c', 'tuberculos', 12, 60), p('d', 'limpieza', 0, null), p('e', 'verduras', 5, 45)];

describe('cuánto falta para que baje', () => {
  it('se mide desde el último tramo alcanzado', () => {
    expect(dropFill(p('x', 'v', 175, null, [{ from: 0, price: 3 }, { from: 100, price: 2 }, { from: 250, price: 1 }]))).toBe(0.5);
  });
  it('null cuando ya tiene el mejor precio', () => expect(dropFill(list[2])).toBeNull());
});

describe('«Están por bajar»', () => {
  it('solo los que ya empezaron, del más cercano al más lejano', () => expect(nearDrop(list).map((x) => x.id)).toEqual(['b', 'e', 'a']));
  it('se puede limitar', () => expect(nearDrop(list, 2).map((x) => x.id)).toEqual(['b', 'e']));
});

describe('grupos de la tienda', () => {
  it('un grupo trae solo sus productos', () => expect(inGroup(list, 'tuberculos').map((x) => x.id)).toEqual(['a', 'c']));
  it('ofertas: los que ahorran frente al súper, del que más al que menos', () => expect(inGroup(list, 'ofertas').map((x) => x.id)).toEqual(['c', 'e', 'a']));
});

describe('chips de la categoría', () => {
  it('Todo respeta el orden', () => expect(applyChip(list, 'todo').map((x) => x.id)).toEqual(['a', 'b', 'c', 'd', 'e']));
  it('Más ahorro primero; sin precio del súper al final', () => expect(applyChip(list, 'ahorro').map((x) => x.id)).toEqual(['c', 'e', 'a', 'b', 'd']));
  it('Por bajar deja fuera los que ya tienen el mejor precio', () => expect(applyChip(list, 'por-bajar').map((x) => x.id)).toEqual(['b', 'e', 'a', 'd']));
});

describe('día de entrega (hora de Lima)', () => {
  it('el sábado de esa semana', () => {
    expect(deliveryDay(new Date('2026-11-10T10:00:00-05:00'))).toBe('sáb 14 nov');
    expect(deliveryDay(new Date('2026-11-14T08:00:00-05:00'))).toBe('sáb 14 nov');
  });
  it('el domingo ya cuenta el sábado siguiente', () => expect(deliveryDay(new Date('2026-11-15T12:00:00-05:00'))).toBe('sáb 21 nov'));
});

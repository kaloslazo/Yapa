import { describe, expect, it } from 'vitest';
import { drawableZones, focusZoneIds, groupColors, marginLabel, unionLabel, unionReason } from './zoneMap';

describe('MP-A..MP-C · colores por grupo', () => {
  it('MP-A: mismo grupo, mismo color', () => {
    const colors = groupColors(['G-LINCE', 'G-LINCE', 'G-JM']);
    expect(colors['G-LINCE']).toBe(groupColors(['G-LINCE'])['G-LINCE']);
  });
  it('MP-B: grupos distintos, colores distintos', () => {
    const colors = groupColors(['G-LINCE', 'G-JM', 'G-LV']);
    expect(new Set(Object.values(colors)).size).toBe(3);
  });
  it('MP-C: agregar un grupo no cambia los colores ya dados', () => {
    const two = groupColors(['G-LINCE', 'G-JM']);
    const three = groupColors(['G-LINCE', 'G-JM', 'G-LV']);
    expect(three['G-LINCE']).toBe(two['G-LINCE']);
    expect(three['G-JM']).toBe(two['G-JM']);
  });
});

describe('MP-D · zonas dibujables', () => {
  it('descarta las que no tienen ubicación', () => {
    const zones = [{ id: 'a', lat: -12.08, lon: -77.03 }, { id: 'b', lat: null, lon: -77.03 }, { id: 'c', lat: -12.1, lon: -77.04 }];
    expect(drawableZones(zones).map((z) => z.id)).toEqual(['a', 'c']);
  });
});

describe('MP-E y MP-F · motivos en palabras', () => {
  it('traduce los códigos conocidos', () => {
    expect(unionReason('CYCLE_CLOSED')).toBe('Solo se unen zonas con el ciclo abierto');
    expect(unionReason('ZONES_TOO_FAR')).toBe('Están muy lejos para compartir camión');
    expect(unionReason('LOCATION_REQUIRED')).toBe('Falta registrar la ubicación de una zona');
  });
  it('un código desconocido no se muestra', () => {
    expect(unionReason('OTRO')).toBe('Hoy no se pueden unir');
    expect(unionReason('OTRO')).not.toContain('OTRO');
  });
});

describe('MP-G y MP-H · etiqueta de la unión', () => {
  it('posible', () => expect(unionLabel(391, '')).toBe('391 m · se puede unir hoy'));
  it('bloqueada', () => expect(unionLabel(455, 'ZONES_TOO_FAR')).toBe('455 m · Están muy lejos para compartir camión'));
});

describe('MP-I y MP-J · margen de la zona', () => {
  it('sin liquidar', () => expect(marginLabel(null)).toBe('Sin liquidar'));
  it('negativo', () => expect(marginLabel('-12.50')).toBe('-S/ 12.50'));
  it('positivo', () => expect(marginLabel('45.00')).toBe('S/ 45.00'));
});

describe('MP-K..MP-M · zonas en foco del mapa', () => {
  const zones = [{ id: 'a', group: 'G1' }, { id: 'b', group: 'G1' }, { id: 'c', group: 'G2' }];
  it('MP-K: las unidas', () => expect([...focusZoneIds(zones, [])].sort()).toEqual(['a', 'b']));
  it('MP-L: las de una unión posible', () => {
    const loose = [{ id: 'a', group: 'G1' }, { id: 'c', group: 'G2' }, { id: 'd', group: 'G3' }];
    expect([...focusZoneIds(loose, [{ a: 'a', b: 'c' }])].sort()).toEqual(['a', 'c']);
  });
  it('MP-M: si no hay nada que enfocar, todas', () => {
    const loose = [{ id: 'a', group: 'G1' }, { id: 'b', group: 'G2' }, { id: 'c', group: 'G3' }];
    expect([...focusZoneIds(loose, [])].sort()).toEqual(['a', 'b', 'c']);
  });
});

import { describe, expect, it } from 'vitest';
import { parseSupplierList, serializeSupplierList, validateSupplierRows } from './supplierDraft';

const list = 'codigo,nombre,categoria,unidad,paso,maximo,proveedor,desde1,precio1\nAJO,Ajo,FRESCOS,kg,0.25,40,SUP-FRESCOS,0,4.80,20,4.40,30,4.10';

describe('PV-01 · edición de la lista del proveedor', () => {
  it('conserva proveedor, decimales y todos los tramos al editar', () => {
    const rows = parseSupplierList(list);
    expect(rows[0].tiers).toHaveLength(3);
    rows[0].maximum = '50';
    expect(serializeSupplierList(rows).split('\n')[1]).toBe('AJO,Ajo,FRESCOS,kg,0.25,50,SUP-FRESCOS,0,4.80,20,4.40,30,4.10');
    expect(validateSupplierRows(rows)).toEqual([]);
  });
  it('señala códigos duplicados, stock no múltiplo y precios que no bajan', () => {
    const rows = parseSupplierList(list);
    rows[0].maximum = '0.3';
    rows[0].tiers[1].price = '5';
    rows.push({ ...rows[0], tiers: [...rows[0].tiers] });
    expect(validateSupplierRows(rows).join(' ')).toMatch(/repetido/);
    expect(validateSupplierRows(rows).join(' ')).toMatch(/múltiplo/);
    expect(validateSupplierRows(rows).join(' ')).toMatch(/menor/);
  });
  it('no permite comas, saltos de línea, unidad fraccionada ni números no finitos', () => {
    const rows = parseSupplierList(list);
    rows[0].name = 'Ajo, especial\nnuevo';
    rows[0].unit = 'unidad';
    rows[0].maximum = 'Infinity';
    expect(validateSupplierRows(rows).length).toBeGreaterThan(0);
    expect(() => serializeSupplierList(rows)).toThrow();
  });
  it('rechaza una lista vacía o un formato incompleto sin descartar filas', () => {
    expect(validateSupplierRows([]).length).toBeGreaterThan(0);
    expect(() => parseSupplierList('AJO,Ajo,FRESCOS,kg,1,5')).toThrow();
  });
});

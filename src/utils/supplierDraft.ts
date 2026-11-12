export interface SupplierRow {
  code: string; name: string; category: string; unit: string; step: string; maximum: string; supplier: string;
  tiers: Array<{ from: string; price: string }>;
}
const HEADER = 'codigo,nombre,categoria,unidad,paso,maximo,proveedor,desde1,precio1';

export function newSupplierRow(): SupplierRow {
  return { code: '', name: '', category: 'FRESCOS', unit: 'kg', step: '1', maximum: '', supplier: '', tiers: [{ from: '0', price: '' }] };
}

export function parseSupplierList(text: string): SupplierRow[] {
  return text.split(/\r?\n/).filter(l => l.trim() && !l.trim().toLowerCase().startsWith('codigo,')).map(line => {
    const cells = line.split(',').map(c => c.trim());
    if (cells.length < 9 || (cells.length - 7) % 2) throw new Error('La lista contiene una fila incompleta. No se ha modificado.');
    const [code, name, category, unit, step, maximum, supplier] = cells;
    return { code, name, category, unit, step, maximum, supplier, tiers: cells.slice(7).reduce<SupplierRow['tiers']>((all, c, i, rest) => i % 2 ? all : [...all, { from: c, price: rest[i + 1] }], []) };
  });
}

const numeric = (v: string) => /^\d+(\.\d+)?$/.test(v) && Number.isFinite(Number(v));
export function validateSupplierRows(rows: SupplierRow[]): string[] {
  if (!rows.length) return ['Añade al menos un producto.'];
  const errors: string[] = [];
  const codes = new Set<string>();
  rows.forEach((row, i) => {
    const prefix = `Producto ${i + 1}`;
    if (!row.code.trim() || !row.name.trim()) errors.push(`${prefix}: completa código y nombre.`);
    if ([row.code, row.name, row.category, row.unit, row.supplier].some(v => /[,\r\n]/.test(v))) errors.push(`${prefix}: usa texto sin comas ni saltos de línea.`);
    if (codes.has(row.code.trim())) errors.push(`${prefix}: código repetido.`);
    codes.add(row.code.trim());
    if (!['FRESCOS', 'LIMPIEZA'].includes(row.category)) errors.push(`${prefix}: elige una categoría válida.`);
    if (!['kg', 'unidad'].includes(row.unit) || (row.unit === 'unidad' && !Number.isInteger(Number(row.step)))) errors.push(`${prefix}: las unidades se venden en pasos enteros.`);
    const step = Number(row.step), maximum = Number(row.maximum);
    if (!numeric(row.step) || !numeric(row.maximum) || step <= 0 || maximum <= 0 || Math.abs(maximum / step - Math.round(maximum / step)) > 1e-8) errors.push(`${prefix}: la cantidad disponible debe ser positiva y múltiplo del paso.`);
    if (!row.tiers.length || row.tiers.some((t, j) => !numeric(t.from) || !numeric(t.price) || Number(t.price) <= 0 || (j === 0 ? Number(t.from) !== 0 : Number(t.from) <= Number(row.tiers[j - 1].from) || Number(t.price) >= Number(row.tiers[j - 1].price)))) errors.push(`${prefix}: empieza desde 0; cada tramo debe tener una cantidad mayor y un precio menor.`);
  });
  return errors;
}

export function serializeSupplierList(rows: SupplierRow[]): string {
  const errors = validateSupplierRows(rows);
  if (errors.length) throw new Error(errors.join(' '));
  return [HEADER, ...rows.map(r => [r.code.trim(), r.name.trim(), r.category, r.unit, r.step, r.maximum, r.supplier, ...r.tiers.flatMap(t => [t.from, t.price])].join(','))].join('\n');
}

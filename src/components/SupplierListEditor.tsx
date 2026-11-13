import { useRef, useState, type FormEvent } from 'react';
import { newSupplierRow, parseSupplierList, serializeSupplierList, validateSupplierRows, type SupplierRow } from '../utils/supplierDraft';
import { Icon } from './Icon';
import { ProductThumb } from './ProductThumb';

interface Props { initialText: string; busy: boolean; onSubmit: (text: string) => Promise<boolean>; resubmit: boolean }

// Edita un borrador; solo el endpoint existente puede enviarlo para revisión.
export function SupplierListEditor({ initialText, busy, onSubmit, resubmit }: Props) {
  const [initial] = useState(() => {
    try { return { rows: parseSupplierList(initialText), error: '' }; }
    catch (error) { return { rows: [], error: error instanceof Error ? error.message : 'No se pudo leer la lista.' }; }
  });
  const [rows, setRows] = useState(() => initial.rows.map((row, id) => ({ id, row })));
  const [fresh, setFresh] = useState<number[]>([]); // S-332: la clave solo se pide al crear un producto
  const nextId = useRef(rows.length);
  const [expanded, setExpanded] = useState<number[]>(rows.length ? [0] : []);
  const [errors, setErrors] = useState<string[]>([]);
  const [dirty, setDirty] = useState(false);
  const change = (id: number, row: SupplierRow) => { setRows(all => all.map(r => r.id === id ? { id, row } : r)); setDirty(true); };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const problems = validateSupplierRows(rows.map(r => r.row));
    setErrors(problems);
    if (problems.length) return;
    if (await onSubmit(serializeSupplierList(rows.map(r => r.row)))) setDirty(false);
  };
  if (initial.error) return <p role="alert">{initial.error} Conservamos tu lista original. Recarga la página o consulta al equipo antes de editar.</p>;
  return (
    <form className="supplier-editor" onSubmit={event => void submit(event)} noValidate>
      <p className="partner-muted">Revisa tu disponibilidad y tus precios por volumen. Los cambios se publican cuando el equipo los aprueba.</p>
      <div className="supplier-editor-toolbar"><strong>{rows.length} {rows.length === 1 ? 'producto' : 'productos'}</strong><span role="status">{dirty ? 'Borrador con cambios sin enviar' : 'Lista lista para revisar'}</span></div>
      {errors.length ? <div className="supplier-errors" role="alert"><strong>Revisa estos datos antes de enviar</strong><ul>{errors.map((error, i) => <li key={i}>{error}</li>)}</ul></div> : null}
      <fieldset disabled={busy} className="supplier-editor-fields"><legend className="sr-only">Productos de tu propuesta</legend>
        {rows.map(({ id, row }, index) => {
          const field = (label: string, key: 'code' | 'name' | 'step' | 'maximum', decimal = false) => <label className="checkout-field"><span>{label}</span><input aria-label={`${label}, producto ${index + 1}`} value={row[key]} inputMode={decimal ? 'decimal' : undefined} onChange={e => change(id, { ...row, [key]: e.target.value })} /></label>;
          return <details className="supplier-product" key={id} open={expanded.includes(id)} onToggle={event => { const open = event.currentTarget.open; setExpanded(all => open === all.includes(id) ? all : open ? [...all, id] : all.filter(n => n !== id)); }}>
            <summary>{fresh.includes(id) ? null : <ProductThumb id={row.code} size={40} />}<span><strong>{row.name || `Nuevo producto ${index + 1}`}</strong><small>{row.maximum || '0'} {row.unit === 'kg' ? 'kg disponibles' : 'unidades disponibles'}</small></span><span className="supplier-product-price">{row.tiers[0]?.price ? `S/ ${row.tiers[0].price} / ${row.unit === 'kg' ? 'kg' : 'u.'}` : 'Sin precio'}</span><Icon name="plus" size={18} /></summary>
            <div className="supplier-product-content">
              <div className="form-grid">
                {fresh.includes(id) ? field('Código (sin espacios, ej. PAPA-HUAYRO)', 'code') : null}{field('Nombre del producto', 'name')}
                <label className="checkout-field"><span>Categoría</span><select aria-label={`Categoría, producto ${index + 1}`} value={row.category} onChange={e => change(id, { ...row, category: e.target.value })}><option value="FRESCOS">Frescos</option><option value="LIMPIEZA">Limpieza</option></select></label>
                <label className="checkout-field"><span>Vendo por</span><select aria-label={`Unidad, producto ${index + 1}`} value={row.unit} onChange={e => change(id, { ...row, unit: e.target.value })}><option value="kg">Peso (kg)</option><option value="unidad">Unidad</option></select></label>
                {field(`Paso de venta (${row.unit === 'kg' ? 'kg' : 'unidades'})`, 'step', true)}{field(`Cantidad disponible (${row.unit === 'kg' ? 'kg' : 'unidades'})`, 'maximum', true)}
              </div>
              <p className="supplier-field-hint">El paso es la cantidad mínima que se puede sumar: por ejemplo, 0.25 kg o 1 unidad.</p>
              <fieldset className="supplier-tiers"><legend>Precios por volumen</legend>
                {row.tiers.map((tier, j) => <div className="supplier-tier" key={j}>
                  <label className="checkout-field"><span>Desde ({row.unit === 'kg' ? 'kg' : 'unidades'})</span><input aria-label={`Desde, tramo ${j + 1}, producto ${index + 1}`} inputMode="decimal" value={tier.from} readOnly={j === 0} onChange={e => change(id, { ...row, tiers: row.tiers.map((t, n) => n === j ? { ...t, from: e.target.value } : t) })} /></label>
                  <label className="checkout-field"><span>Precio por {row.unit === 'kg' ? 'kg' : 'unidad'} (S/)</span><input aria-label={`Precio, tramo ${j + 1}, producto ${index + 1}`} inputMode="decimal" value={tier.price} onChange={e => change(id, { ...row, tiers: row.tiers.map((t, n) => n === j ? { ...t, price: e.target.value } : t) })} /></label>
                  {j > 0 ? <button className="text-button" type="button" aria-label={`Quitar tramo ${j + 1}, producto ${index + 1}`} onClick={() => change(id, { ...row, tiers: row.tiers.filter((_, n) => n !== j) })}>Quitar</button> : <span className="supplier-field-hint">Precio inicial</span>}
                </div>)}
                <button className="secondary-button" type="button" onClick={() => change(id, { ...row, tiers: [...row.tiers, { from: '', price: '' }] })}>Añadir precio por volumen</button>
              </fieldset>
              <button className="text-button" type="button" onClick={() => { setRows(all => all.filter(r => r.id !== id)); setDirty(true); }}>Quitar {row.name || 'producto'} del borrador</button>
            </div>
          </details>;
        })}
        <button className="secondary-button" type="button" onClick={() => { const id = nextId.current++; setRows(all => [...all, { id, row: newSupplierRow() }]); setFresh(all => [...all, id]); setExpanded(all => [...all, id]); setDirty(true); }}><Icon name="plus" size={18} />Añadir producto</button>
      </fieldset>
      <button className="primary-button" type="submit" disabled={busy}>{busy ? 'Enviando…' : resubmit ? 'Enviar de nuevo para revisión' : 'Enviar para revisión'}</button>
    </form>
  );
}

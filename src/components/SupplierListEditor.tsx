import { useRef, useState, type FormEvent } from 'react';
import { api } from '../services/api';
import { newSupplierRow, parseSupplierList, serializeSupplierList, validateSupplierRows, type SupplierRow } from '../utils/supplierDraft';
import { Icon } from './Icon';
import { ProductThumb } from './ProductThumb';
import { SupplierStock, type StockTotal } from './SupplierStock';

interface QuoteRow { codigo: string; nombre: string; categoria: string; unidad: string; paso: string; maximo: string; tramos: Array<{ desde: string; precio: string }> }
interface QuoteRead { filas: QuoteRow[]; nuevos: string[]; avisos: string[]; fuente: 'ia' | 'reglas' }

// iteración 69, LP-01: la foto o el mensaje de la cotización llenan el borrador; el proveedor revisa y envía como siempre
function QuoteReader({ disabled, onRead }: { disabled: boolean; onRead: (read: QuoteRead) => string }) {
  const [text, setText] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);
  const [state, setState] = useState<{ busy: boolean; summary: string; warnings: string[]; error: string }>({ busy: false, summary: '', warnings: [], error: '' });
  const read = async () => {
    if (!text.trim() && !photo) { setState({ busy: false, summary: '', warnings: [], error: 'Pega el mensaje o elige la foto de tu cotización.' }); return; }
    const form = new FormData();
    if (text.trim()) form.set('texto', text.trim());
    if (photo) form.set('foto_archivo', photo);
    setState({ busy: true, summary: '', warnings: [], error: '' });
    try {
      const result = await api.post<QuoteRead>('/api/proveedor/lista/leer', form);
      setState({ busy: false, summary: onRead(result), warnings: result.avisos, error: '' });
    } catch (error) {
      setState({ busy: false, summary: '', warnings: [], error: error instanceof Error ? error.message : 'No pudimos leer la cotización.' });
    }
  };
  return (
    <section className="quote-reader" aria-labelledby="quote-reader-title">
      <div className="quote-reader-head"><Icon name="sparkle" size={18} /><div><h3 id="quote-reader-title">Leer cotización con IA</h3><p>Sube la foto de tu pizarra o lista, o pega el mensaje que mandas por WhatsApp. Llenamos el borrador y tú lo revisas.</p></div></div>
      <textarea value={text} onChange={e => setText(e.target.value)} rows={3} maxLength={4000} placeholder={'Papa amarilla S/ 3.40 el kg, hay 300 kg\ndesde 100 kg a 3.10'} aria-label="Mensaje de tu cotización" disabled={disabled || state.busy} />
      <div className="quote-reader-actions">
        <label className="photo-field"><Icon name="camera" size={18} /><span>{photo ? photo.name : 'Foto de la cotización'}</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={e => setPhoto(e.currentTarget.files?.[0] ?? null)} disabled={disabled || state.busy} /></label>
        <button className="secondary-button" type="button" onClick={() => void read()} disabled={disabled || state.busy}>{state.busy ? 'Leyendo…' : 'Leer cotización'}</button>
      </div>
      {state.error ? <p className="quote-reader-error" role="alert">{state.error}</p> : null}
      {state.summary ? <p className="quote-reader-summary" role="status">{state.summary}</p> : null}
      {state.warnings.length ? <ul className="quote-reader-warnings">{state.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul> : null}
    </section>
  );
}

interface Props { initialText: string; busy: boolean; onSubmit: (text: string) => Promise<boolean>; resubmit: boolean; cycle?: string }

// Edita un borrador; solo el endpoint existente puede enviarlo para revisión.
export function SupplierListEditor({ initialText, busy, onSubmit, resubmit, cycle }: Props) {
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
  const [stockWarning,setStockWarning]=useState('');
  const change = (id: number, row: SupplierRow) => { setRows(all => all.map(r => r.id === id ? { id, row } : r)); setDirty(true); };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const problems = validateSupplierRows(rows.map(r => r.row));
    setErrors(problems);
    if (problems.length) return;
    if (await onSubmit(serializeSupplierList(rows.map(r => r.row)))) setDirty(false);
  };
  const fill = (read: QuoteRead) => {
    let updated = 0, added = 0;
    const known = new Map(rows.map(r => [r.row.code, r]));
    const next = [...rows];
    const freshIds: number[] = [];
    for (const f of read.filas) {
      const tiers = f.tramos.map(t => ({ from: t.desde, price: t.precio }));
      const current = known.get(f.codigo);
      if (current) { updated++; next[next.indexOf(current)] = { id: current.id, row: { ...current.row, maximum: f.maximo, tiers } }; continue; }
      added++;
      const id = nextId.current++;
      freshIds.push(id);
      next.push({ id, row: { ...newSupplierRow(), code: f.codigo, name: f.nombre, category: f.categoria, unit: f.unidad, step: f.paso, maximum: f.maximo, tiers } });
    }
    setRows(next);
    setFresh(all => [...all, ...freshIds]);
    setExpanded(all => [...all, ...freshIds]);
    if (updated || added) setDirty(true);
    const how = read.fuente === 'ia' ? 'Leído con IA' : 'Leído con reglas simples';
    return updated || added ? `${how}: ${updated} ${updated === 1 ? 'actualizado' : 'actualizados'} y ${added} ${added === 1 ? 'nuevo' : 'nuevos'}. Revisa cada producto antes de enviar.` : `${how}: no encontramos productos con precio. Prueba con otra foto o pega el texto.`;
  };
  const applyStock = (totals:StockTotal[]) => {
    const quantities=new Map(totals.map(p=>[p.id,p]));
    const incompatible=rows.filter(p=>quantities.has(p.row.code)&&quantities.get(p.row.code)!.unidad!==p.row.unit);
    setStockWarning(incompatible.length?'Hay productos con una unidad distinta en el borrador. Sus cantidades no se aplicaron: revisa la unidad antes de enviar.':'');
    setRows(current=>current.map(p=>quantities.get(p.row.code)?.unidad===p.row.unit?{...p,row:{...p.row,maximum:quantities.get(p.row.code)!.disponible}}:p));
    if(totals.length)setDirty(true);
  };
  if (initial.error) return <p role="alert">{initial.error} Conservamos tu lista original. Recarga la página o consulta al equipo antes de editar.</p>;
  return (
    <>
    {cycle ? <SupplierStock cycle={cycle} candidates={rows.filter(p=>p.row.code).map(p=>({id:p.row.code,name:p.row.name,unit:p.row.unit}))} onApply={applyStock}/> : null}
    {stockWarning?<p role="alert">{stockWarning}</p>:null}
    <QuoteReader disabled={busy} onRead={fill} />
    <form className="supplier-editor" onSubmit={event => void submit(event)} noValidate>
      <p className="partner-muted">Revisa tu disponibilidad y tus precios por volumen. Los cambios se publican cuando el equipo los aprueba.</p>
      <div className="supplier-editor-toolbar"><strong>{rows.length} {rows.length === 1 ? 'producto' : 'productos'}</strong><span role="status">{dirty ? 'Borrador con cambios sin enviar' : 'Sin cambios por enviar'}</span></div>
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
              <details className="supplier-volume"><summary>Precios por volumen de {row.name || "este producto"}</summary><fieldset className="supplier-tiers"><legend className="sr-only">Precios por volumen</legend>
                {row.tiers.map((tier, j) => <div className="supplier-tier" key={j}>
                  <label className="checkout-field"><span>Desde ({row.unit === 'kg' ? 'kg' : 'unidades'})</span><input aria-label={`Desde, tramo ${j + 1}, producto ${index + 1}`} inputMode="decimal" value={tier.from} readOnly={j === 0} onChange={e => change(id, { ...row, tiers: row.tiers.map((t, n) => n === j ? { ...t, from: e.target.value } : t) })} /></label>
                  <label className="checkout-field"><span>Precio por {row.unit === 'kg' ? 'kg' : 'unidad'} (S/)</span><input aria-label={`Precio, tramo ${j + 1}, producto ${index + 1}`} inputMode="decimal" value={tier.price} onChange={e => change(id, { ...row, tiers: row.tiers.map((t, n) => n === j ? { ...t, price: e.target.value } : t) })} /></label>
                  {j > 0 ? <button className="text-button" type="button" aria-label={`Quitar tramo ${j + 1}, producto ${index + 1}`} onClick={() => change(id, { ...row, tiers: row.tiers.filter((_, n) => n !== j) })}>Quitar</button> : <span className="supplier-field-hint">Precio inicial</span>}
                </div>)}
                <button className="secondary-button" type="button" onClick={() => change(id, { ...row, tiers: [...row.tiers, { from: '', price: '' }] })}>Añadir precio por volumen</button>
              </fieldset></details>
              <button className="text-button" type="button" onClick={() => { setRows(all => all.filter(r => r.id !== id)); setDirty(true); }}>Quitar {row.name || 'producto'} del borrador</button>
            </div>
          </details>;
        })}
        <button className="secondary-button" type="button" onClick={() => { const id = nextId.current++; setRows(all => [...all, { id, row: newSupplierRow() }]); setFresh(all => [...all, id]); setExpanded(all => [...all, id]); setDirty(true); }}><Icon name="plus" size={18} />Añadir producto</button>
      </fieldset>
      <button className="primary-button" type="submit" disabled={busy}>{busy ? 'Enviando…' : resubmit ? 'Enviar de nuevo para revisión' : 'Enviar para revisión'}</button>
    </form>
    </>
  );
}

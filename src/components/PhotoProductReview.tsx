import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { PhotoPreview, usePhotoPreview } from './PhotoForm';
import { matchPhotoProduct, photoKind, type PhotoCandidate } from '../utils/photoMatches';
import './PhotoProductReview.css';

export type ProductCount = { producto: string; cantidad: number; confianza?: number; codigo?: string; confirmado?: boolean; peso?: string };
const PRODUCTS = ['papa', 'cebolla', 'ajo', 'zanahoria', 'limon', 'camote', 'otro'];
export function PhotoProductReview({ onConfirm, label = 'Confirmar conteo de referencia', candidates, onMatchesChange, photoLabel = 'Elegir foto para revisar', requireWeight = false }: {
 onConfirm?: (file: File, products: ProductCount[]) => Promise<boolean>; label?: string; candidates?: PhotoCandidate[];
 onMatchesChange?: (codes: string[]) => void; photoLabel?: string; requireWeight?: boolean;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [products, setProducts] = useState<ProductCount[]>([]);
  const [state, setState] = useState<'idle' | 'analyzing' | 'saving' | 'confirmed'>('idle');
  const [error, setError] = useState('');
  const version = useRef(0), saving = useRef(false);
  const { preview, choose } = usePhotoPreview();
  useEffect(() => () => { version.current++; }, []);
  useEffect(() => { onMatchesChange?.([...new Set(products.filter(p => p.confirmado && p.codigo).map(p => p.codigo!))]); }, [products, onMatchesChange]);
  const analyze = async (photo: File | undefined) => {
    const request = ++version.current;
    setFile(photo ?? null); setProducts([]); setError(''); choose(photo); setState(photo ? 'analyzing' : 'idle');
    if (!photo) return;
    const form = new FormData(); form.set('foto_archivo', photo);
    try {
      const response = await api.post<{ productos: ProductCount[] }>('/api/vision/analizar', form);
      if (request === version.current) setProducts((response.productos ?? []).map(p => candidates ? { ...p, codigo: matchPhotoProduct(p.producto, candidates), confirmado: false } : p));
    } catch (problem) {
      if (request === version.current) setError(problem instanceof Error ? problem.message : 'No pudimos analizar. Completa la revisión manualmente.');
    } finally { if (request === version.current) setState('idle'); }
  };
  const update = (i: number, changes: Partial<ProductCount>) => { setProducts(rows => rows.map((p, index) => i === index ? { ...p, ...changes, ...(candidates ? { confirmado: false } : {}), confianza: undefined } : p)); setState('idle'); };
  const rowValid = (p: ProductCount) => Number.isInteger(p.cantidad) && p.cantidad >= 1 && p.cantidad <= 300 && (!candidates || candidates.some(c => c.id === p.codigo)) && (!requireWeight || candidates?.find(c => c.id === p.codigo)?.unit !== 'kg' || (Number(p.peso) > 0 && Number.isFinite(Number(p.peso))));
  const valid = file && products.length > 0 && products.every(p => rowValid(p) && (!candidates || p.confirmado));
  const locked = state === 'analyzing' || state === 'saving', reviewLocked = locked || state === 'confirmed';
  const confirm = async () => {
    if (!file || !valid || locked || saving.current) return;
    saving.current = true; setState('saving'); setError('');
    try { const ok = onConfirm ? await onConfirm(file, products) : true; setState(ok ? 'confirmed' : 'idle'); if (!ok) setError('No se pudo guardar. Conservamos la foto y tu revisión para reintentar.'); }
    catch (problem) { setState('idle'); setError(problem instanceof Error ? problem.message : 'No se pudo confirmar. Conservamos tu foto y las correcciones para reintentar.'); }
    finally { saving.current = false; }
  };
  return <section className="photo-product-review" aria-label="Revisión de productos por foto">
    <h3>Foto de la bolsa y sus productos</h3>
    <p>El detector se activa al elegir la foto. Estima papa, cebolla, ajo y zanahoria; corrige o añade lo que falte. Las unidades visibles no son kilos.</p>
    <label className="photo-field pack-camera"><span>{photoLabel}</span><input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" disabled={state === 'saving'} onChange={event => void analyze(event.target.files?.[0])} /></label>
    <PhotoPreview src={preview} />
    {state === 'analyzing' ? <p role="status">Analizando la foto…</p> : null}
    {error ? <p role="alert">{error}</p> : null}
    {file && !locked && !products.length ? <p>No hay productos sugeridos. Añádelos manualmente; la foto no se guarda hasta confirmar.</p> : null}
    {products.map((p, i) => <div className="photo-product-row" key={i}>
      <label>{candidates ? `Corresponde a, producto ${i + 1}` : `Producto ${i + 1}`}<select value={candidates ? p.codigo ?? '' : p.producto} disabled={reviewLocked} onChange={e => candidates ? update(i, { codigo: e.target.value, producto: photoKind(candidates.find(c => c.id === e.target.value)?.name ?? '') }) : update(i, { producto: e.target.value })}>
        {candidates ? <><option value="">Elige el producto exacto</option>{candidates.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</> : PRODUCTS.map(name => <option key={name} value={name}>{name}</option>)}
      </select></label>
      <label>Unidades visibles {i + 1}<input type="number" min="1" max="300" step="1" value={Number.isFinite(p.cantidad) ? p.cantidad : ''} disabled={reviewLocked} onChange={e => update(i, { cantidad: e.target.value === '' ? NaN : Number(e.target.value) })} /></label>
      {requireWeight && candidates?.find(c => c.id === p.codigo)?.unit === 'kg' ? <label>Peso medido en kg, producto {i + 1}<input type="number" min="0.001" step="any" value={p.peso ?? ''} disabled={reviewLocked} onChange={e => update(i, { peso: e.target.value })} /></label> : null}
      {candidates ? <button className="photo-row-check" type="button" disabled={reviewLocked || !rowValid(p)} aria-label={`Confirmar producto ${i + 1}`} aria-pressed={Boolean(p.confirmado)} onClick={() => setProducts(rows => rows.map((row, j) => i === j ? { ...row, confirmado: !row.confirmado } : row))}>{p.confirmado ? '✓ Confirmado' : '✓ Confirmar'}</button> : null}
      <button type="button" disabled={reviewLocked} onClick={() => { setProducts(rows => rows.filter((_, j) => i !== j)); setState('idle'); }} aria-label={`Quitar producto ${i + 1}`}>Quitar</button>
      {p.confianza != null ? <small>Sugerido: {p.producto} · puntuación {Math.round(p.confianza * 100)} %. Requiere revisión.</small> : null}
    </div>)}
    {file ? <div className="photo-product-actions"><button type="button" disabled={reviewLocked} onClick={() => { const c=candidates?.[0]; setProducts(rows => [...rows, { producto: c ? photoKind(c.name) : 'papa', cantidad: 1, ...(candidates ? { codigo: c?.id ?? '', confirmado: false } : {}) }]); setState('idle'); }}>Añadir producto manualmente</button><button type="button" className="primary-button" disabled={!valid || locked || state === 'confirmed'} onClick={() => void confirm()}>{state === 'saving' ? 'Confirmando…' : label}</button></div> : null}
    {state === 'confirmed' ? <p role="status">Confirmado por ti: {products.map(p => `${candidates?.find(c => c.id === p.codigo)?.name ?? p.producto}: ${p.cantidad}`).join(' · ')}. El conteo no modifica pesos ni precios del pedido.</p> : null}
  </section>;
}

import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { PhotoPreview, usePhotoPreview } from './PhotoForm';
import './PhotoProductReview.css';

export type ProductCount = { producto: string; cantidad: number; confianza?: number };
const PRODUCTS = ['papa', 'cebolla', 'ajo', 'zanahoria', 'limon', 'camote', 'otro'];
export function PhotoProductReview({ onConfirm, label = 'Confirmar conteo de referencia' }: { onConfirm?: (file: File, products: ProductCount[]) => Promise<boolean>; label?: string }) {
  const [file, setFile] = useState<File | null>(null);
  const [products, setProducts] = useState<ProductCount[]>([]);
  const [state, setState] = useState<'idle' | 'analyzing' | 'saving' | 'confirmed'>('idle');
  const [error, setError] = useState('');
  const version = useRef(0);
  const { preview, choose } = usePhotoPreview();
  useEffect(() => () => { version.current++; }, []);
  const analyze = async (photo: File | undefined) => {
    const request = ++version.current;
    setFile(photo ?? null); setProducts([]); setError(''); choose(photo); setState(photo ? 'analyzing' : 'idle');
    if (!photo) return;
    const form = new FormData(); form.set('foto_archivo', photo);
    try {
      const response = await api.post<{ productos: ProductCount[] }>('/api/vision/analizar', form);
      if (request === version.current) setProducts(response.productos);
    } catch (problem) {
      if (request === version.current) setError(problem instanceof Error ? problem.message : 'No pudimos analizar. Completa la revisión manualmente.');
    } finally { if (request === version.current) setState('idle'); }
  };
  const update = (i: number, changes: Partial<ProductCount>) => { setProducts(rows => rows.map((p, index) => i === index ? { ...p, ...changes, confianza: undefined } : p)); setState('idle'); };
  const valid = file && products.length > 0 && products.every(p => PRODUCTS.includes(p.producto) && Number.isInteger(p.cantidad) && p.cantidad >= 1 && p.cantidad <= 300);
  const locked = state === 'analyzing' || state === 'saving';
  const reviewLocked = locked || state === 'confirmed';
  const confirm = async () => {
    if (!file || !valid || locked) return;
    setState('saving'); setError('');
    try { const ok = onConfirm ? await onConfirm(file, products) : true; setState(ok ? 'confirmed' : 'idle'); }
    catch { setState('idle'); setError('No se pudo confirmar. Conservamos tu foto y las correcciones para reintentar.'); }
  };
  return <section className="photo-product-review" aria-label="Revisión de productos por foto">
    <h3>Revisar productos con una foto</h3>
    <p>Detecta papa, cebolla, ajo y zanahoria. Sugiere unidades visibles, no kilos. Revisa y corrige antes de confirmar.</p>
    <label className="photo-field"><span>Elegir foto para revisar</span><input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" disabled={state === 'saving'} onChange={event => void analyze(event.target.files?.[0])} /></label>
    <PhotoPreview src={preview} />
    {state === 'analyzing' ? <p role="status">Analizando la foto…</p> : null}
    {error ? <p role="alert">{error}</p> : null}
    {file && !locked && !products.length ? <p>No hay productos sugeridos. Puedes añadirlos manualmente; esto no significa que la foto esté vacía.</p> : null}
    {products.map((p, i) => <div className="photo-product-row" key={i}>
      <label>Producto {i + 1}<select value={p.producto} disabled={reviewLocked} onChange={e => update(i, { producto: e.target.value })}>{PRODUCTS.map(name => <option key={name} value={name}>{name}</option>)}</select></label>
      <label>Unidades visibles {i + 1}<input type="number" min="1" max="300" step="1" value={Number.isFinite(p.cantidad) ? p.cantidad : ''} disabled={reviewLocked} onChange={e => update(i, { cantidad: e.target.value === '' ? NaN : Number(e.target.value) })} /></label>
      <button type="button" disabled={reviewLocked} onClick={() => { setProducts(rows => rows.filter((_, j) => i !== j)); setState('idle'); }} aria-label={`Quitar producto ${i + 1}`}>Quitar</button>
      {p.confianza != null ? <small>Puntuación mínima del detector: {Math.round(p.confianza * 100)} %. No garantiza el conteo.</small> : null}
    </div>)}
    {file ? <div className="photo-product-actions"><button type="button" disabled={reviewLocked} onClick={() => { setProducts(rows => [...rows, { producto: 'papa', cantidad: 1 }]); setState('idle'); }}>Añadir producto manualmente</button><button type="button" className="primary-button" disabled={!valid || locked || state === 'confirmed'} onClick={() => void confirm()}>{state === 'saving' ? 'Confirmando…' : label}</button></div> : null}
    {state === 'confirmed' ? <p role="status">Confirmado por ti: {products.map(p => `${p.producto}: ${p.cantidad}`).join(' · ')}. El conteo es una referencia en esta pantalla; no modifica cantidades ni precios del pedido o catálogo.</p> : null}
  </section>;
}

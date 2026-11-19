import { useEffect, useRef, useState } from 'react';
import { api } from '../services/api';
import { PhotoPreview, usePhotoPreview } from './PhotoForm';
import { matchPhotoProduct, photoKind, type PhotoCandidate } from '../utils/photoMatches';
import { shrinkPhoto } from '../utils/photoResize';
import './PhotoProductReview.css';

export type ProductCount = { producto: string; cantidad: number; confianza?: number; codigo?: string; confirmado?: boolean; peso?: string };
type State = 'idle' | 'analyzing' | 'saving' | 'confirmed';
type Source = 'ia' | 'detector';
type Analysis = { productos: ProductCount[]; fuente?: Source; otros?: string[] };
type Props = {
  onConfirm?: (file: File, products: ProductCount[]) => Promise<boolean>;
  label?: string;
  candidates?: PhotoCandidate[];
  onMatchesChange?: (codes: string[]) => void;
  photoLabel?: string;
  requireWeight?: boolean;
  title?: string;
  photo?: File; // iteración 76: la foto ya se tomó (la bolsa ya está registrada) y aquí solo se revisa
  scope?: string; // dónde deben estar los productos sugeridos: "el pedido", "tu lista"
  context?: Record<string, string>; // iteración 77: { pedido } o { para: 'stock' }, para que la IA reciba esa lista
};

const PRODUCTS = ['papa', 'cebolla', 'ajo', 'zanahoria', 'limon', 'camote', 'otro'];
const MAX_UNITS = 300;
const SOURCE_LABEL: Record<Source, string> = { ia: 'Con IA', detector: 'Con el detector local' };

// S-371: con candidatos, solo queda lo que corresponde a alguno; lo demás se descarta y se cuenta.
// Iteración 77: si la IA ya dio el código del producto, se usa tal cual (no hay que adivinar cuál papa)
function keepKnown(found: ProductCount[], candidates?: PhotoCandidate[]) {
  if (!candidates) return { rows: found, dropped: 0 };
  const fits = (p: ProductCount) => (p.codigo
    ? candidates.some((c) => c.id === p.codigo)
    : candidates.some((c) => photoKind(c.name) === p.producto || photoKind(c.id) === p.producto));
  const known = found.filter(fits);
  const rows = known.map((p) => ({ ...p, codigo: p.codigo || matchPhotoProduct(p.producto, candidates), confirmado: false }));
  return { rows, dropped: found.length - known.length };
}

export function PhotoProductReview({
  onConfirm, label = 'Confirmar conteo de referencia', candidates, onMatchesChange, photoLabel = 'Elegir foto para revisar',
  requireWeight = false, title = 'Foto de la bolsa y sus productos', photo, scope = 'la lista', context,
}: Props) {
  const [file, setFile] = useState<File | null>(photo ?? null);
  const [products, setProducts] = useState<ProductCount[]>([]);
  const [dropped, setDropped] = useState(0);
  const [source, setSource] = useState<Source | null>(null);
  const [others, setOthers] = useState<string[]>([]);
  const [state, setState] = useState<State>('idle');
  const [error, setError] = useState('');
  const version = useRef(0);
  const saving = useRef(false);
  const { preview, choose } = usePhotoPreview();
  useEffect(() => { if (photo) choose(photo); }, [photo]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => { version.current++; }, []);
  useEffect(() => {
    onMatchesChange?.([...new Set(products.filter((p) => p.confirmado && p.codigo).map((p) => p.codigo!))]);
  }, [products, onMatchesChange]);

  const unitOf = (p: ProductCount) => candidates?.find((c) => c.id === p.codigo)?.unit;
  const nameOf = (p: ProductCount) => candidates?.find((c) => c.id === p.codigo)?.name ?? p.producto;

  // S-369 y S-373: elegir la foto no llama al detector
  const pick = (chosen: File | undefined) => {
    version.current++;
    setFile(chosen ?? null);
    setProducts([]);
    setDropped(0);
    setSource(null);
    setOthers([]);
    setError('');
    choose(chosen);
    setState('idle');
  };

  const suggest = async () => {
    if (!file) return;
    const request = ++version.current;
    setProducts([]);
    setDropped(0);
    setSource(null);
    setOthers([]);
    setError('');
    setState('analyzing');
    const form = new FormData();
    for (const [key, value] of Object.entries(context ?? {})) form.set(key, value);
    try {
      form.set('foto_archivo', await shrinkPhoto(file));
      const response = await api.post<Analysis>('/api/vision/analizar', form);
      if (request !== version.current) return;
      const { rows, dropped: left } = keepKnown(response.productos ?? [], candidates);
      setProducts(rows);
      setDropped(left);
      setSource(response.fuente ?? null);
      setOthers(response.otros ?? []);
    } catch (problem) {
      if (request === version.current) setError(problem instanceof Error ? problem.message : 'No pudimos analizar. Completa la revisión manualmente.');
    } finally {
      if (request === version.current) setState('idle');
    }
  };

  const update = (i: number, changes: Partial<ProductCount>) => {
    setProducts((rows) => rows.map((p, index) => (i === index ? { ...p, ...changes, ...(candidates ? { confirmado: false } : {}), confianza: undefined } : p)));
    setState('idle');
  };
  const toggle = (i: number) => setProducts((rows) => rows.map((row, j) => (i === j ? { ...row, confirmado: !row.confirmado } : row)));
  const remove = (i: number) => { setProducts((rows) => rows.filter((_, j) => i !== j)); setState('idle'); };
  const addManual = () => {
    const first = candidates?.[0];
    setProducts((rows) => [...rows, { producto: first ? photoKind(first.name) : 'papa', cantidad: 1, ...(candidates ? { codigo: first?.id ?? '', confirmado: false } : {}) }]);
    setState('idle');
  };

  const weightOk = (p: ProductCount) => !requireWeight || unitOf(p) !== 'kg' || (Number(p.peso) > 0 && Number.isFinite(Number(p.peso)));
  const rowValid = (p: ProductCount) => Number.isInteger(p.cantidad) && p.cantidad >= 1 && p.cantidad <= MAX_UNITS
    && (!candidates || candidates.some((c) => c.id === p.codigo)) && weightOk(p);
  const valid = file && products.length > 0 && products.every((p) => rowValid(p) && (!candidates || p.confirmado));
  const locked = state === 'analyzing' || state === 'saving';
  const reviewLocked = locked || state === 'confirmed';

  const confirm = async () => {
    if (!file || !valid || locked || saving.current) return;
    saving.current = true;
    setState('saving');
    setError('');
    try {
      const ok = onConfirm ? await onConfirm(file, products) : true;
      setState(ok ? 'confirmed' : 'idle');
      if (!ok) setError('No se pudo guardar. Conservamos la foto y tu revisión para reintentar.');
    } catch (problem) {
      setState('idle');
      setError(problem instanceof Error ? problem.message : 'No se pudo confirmar. Conservamos tu foto y las correcciones para reintentar.');
    } finally {
      saving.current = false;
    }
  };

  return <section className="photo-product-review" aria-label="Revisión de productos por foto">
    <h3>{title}</h3>
    <p>Si quieres ayuda, toca «Sugerir con el detector»: la IA revisa la foto con los productos de {scope}. Sin IA, el detector local solo reconoce papa, cebolla, ajo y zanahoria. Corrige o añade lo que falte. Las unidades que se ven no son kilos.</p>
    {photo ? null : <label className="photo-field pack-camera"><span>{photoLabel}</span>
      <input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" disabled={state === 'saving'}
        onChange={(event) => { const chosen = event.target.files?.[0]; event.target.value = ''; pick(chosen); }} /></label>}
    <PhotoPreview src={preview} />
    {state === 'analyzing' ? <p role="status">Analizando la foto…</p> : null}
    {error ? <p role="alert">{error}</p> : null}
    {source ? <p className="photo-source">{SOURCE_LABEL[source]}</p> : null}
    {others.length ? <p className="photo-others">También se ve: {others.join(', ')}</p> : null}
    {dropped ? <p role="status">{dropped === 1 ? `1 sugerencia no está en ${scope} y no se muestra.` : `${dropped} sugerencias no están en ${scope} y no se muestran.`}</p> : null}
    {products.map((p, i) => <div className="photo-product-row" key={i}>
      <label>{candidates ? `Corresponde a, producto ${i + 1}` : `Producto ${i + 1}`}
        <select value={candidates ? p.codigo ?? '' : p.producto} disabled={reviewLocked}
          onChange={(e) => (candidates
            ? update(i, { codigo: e.target.value, producto: photoKind(candidates.find((c) => c.id === e.target.value)?.name ?? '') })
            : update(i, { producto: e.target.value }))}>
          {candidates
            ? <><option value="">Elige el producto exacto</option>{candidates.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</>
            : PRODUCTS.map((name) => <option key={name} value={name}>{name}</option>)}
        </select></label>
      <label>Unidades visibles {i + 1}<input type="number" min="1" max={MAX_UNITS} step="1" value={Number.isFinite(p.cantidad) ? p.cantidad : ''} disabled={reviewLocked}
        onChange={(e) => update(i, { cantidad: e.target.value === '' ? NaN : Number(e.target.value) })} /></label>
      {requireWeight && unitOf(p) === 'kg'
        ? <label>Peso medido en kg, producto {i + 1}<input type="number" min="0.001" step="any" value={p.peso ?? ''} disabled={reviewLocked} onChange={(e) => update(i, { peso: e.target.value })} /></label>
        : null}
      {candidates
        ? <button className="photo-row-check" type="button" disabled={reviewLocked || !rowValid(p)} aria-label={`Confirmar producto ${i + 1}`} aria-pressed={Boolean(p.confirmado)} onClick={() => toggle(i)}>{p.confirmado ? '✓ Confirmado' : '✓ Confirmar'}</button>
        : null}
      <button type="button" disabled={reviewLocked} onClick={() => remove(i)} aria-label={`Quitar producto ${i + 1}`}>Quitar</button>
      {p.confianza != null ? <small>Sugerido: {p.producto} · puntuación {Math.round(p.confianza * 100)} %. Revísalo.</small> : null}
    </div>)}
    {file ? <div className="photo-product-actions">
      <button type="button" disabled={reviewLocked} onClick={() => void suggest()}>Sugerir con el detector</button>
      <button type="button" disabled={reviewLocked} onClick={addManual}>Añadir producto manualmente</button>
      <button type="button" className="primary-button" disabled={!valid || locked || state === 'confirmed'} onClick={() => void confirm()}>{state === 'saving' ? 'Confirmando…' : label}</button>
    </div> : null}
    {state === 'confirmed' ? <p role="status">Confirmado por ti: {products.map((p) => `${nameOf(p)}: ${p.cantidad}`).join(' · ')}. El conteo no cambia pesos ni precios del pedido.</p> : null}
  </section>;
}

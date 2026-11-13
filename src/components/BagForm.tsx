import { useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Icon } from './Icon';

type PendingBag = { id: number; photo: File | null };

// Una foto por bolsa; los reintentos incluyen solo las que no se guardaron.
export function BagForm({ onSend }: { onSend: (form: FormData) => Promise<boolean> }) {
  const nextId = useRef(1);
  const sending = useRef(false);
  const [bags, setBags] = useState<PendingBag[]>([{ id: 0, photo: null }]);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState('');
  const ready = bags.every(bag => bag.photo);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (sending.current || !ready) return;
    sending.current = true;
    setBusy(true); setFeedback('');
    let saved = 0;
    try {
      for (const bag of bags) {
        const form = new FormData();
        form.set('foto_archivo', bag.photo!);
        if (!await onSend(form)) break;
        saved++;
      }
    } catch {
      // El formulario conserva las fotos pendientes aunque falle la conexión.
    } finally {
      if (saved === bags.length) {
        setBags([{ id: nextId.current++, photo: null }]);
      } else {
        setBags(bags.slice(saved));
        setFeedback(`${saved} ${saved === 1 ? 'bolsa guardada' : 'bolsas guardadas'}. Quedan ${bags.length - saved} por confirmar. Reintenta las pendientes.`);
      }
      sending.current = false;
      setBusy(false);
    }
  };

  return <form className="bag-form" onSubmit={submit} aria-label="Agregar bolsas">
    {bags.map((bag, index) => <label className="photo-field" key={bag.id}>
      <Icon name="camera" size={18} /><span>Foto {index + 1}</span>
      <input type="file" accept="image/*" capture="environment" required disabled={busy}
        onChange={event => {
          const photo = event.target.files?.[0] ?? null;
          setBags(current => current.map(item => item.id === bag.id ? { ...item, photo } : item));
        }} />
    </label>)}
    <div className="bag-form-actions">
      <span>Agregar {bags.length === 1 ? 'bolsa' : 'bolsas'}</span>
      <div className="bag-stepper" role="group" aria-label="Bolsas nuevas">
        <button type="button" aria-label="Disminuir bolsas" disabled={busy || bags.length <= 1}
          onClick={() => setBags(current => current.slice(0, -1))}><Icon name="minus" size={16} /></button>
        <output aria-label="Cantidad de bolsas nuevas" aria-live="polite">{bags.length}</output>
        <button type="button" aria-label="Aumentar bolsas" disabled={busy}
          onClick={() => setBags(current => [...current, { id: nextId.current++, photo: null }])}><Icon name="plus" size={16} /></button>
      </div>
      <button className="bag-confirm" type="submit" aria-label="Confirmar bolsas" title="Confirmar bolsas" disabled={busy || !ready}>
        <Icon name="check" size={18} /><span className="sr-only">{busy ? 'Guardando…' : 'Confirmar'}</span>
      </button>
    </div>
    <small className="bag-form-note">{busy ? 'Guardando bolsas…' : 'Una foto por bolsa nueva.'}</small>
    {feedback ? <small role="status">{feedback}</small> : null}
  </form>;
}

import { useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { Icon } from './Icon';

// foto obligatoria con la cámara del celular (S-151); la usan el panel y el reparto
export function PhotoForm({ label, onSend, children, big = false }: { label: string; onSend: (form: FormData) => Promise<boolean>; children?: ReactNode; big?: boolean }) {
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const element = event.currentTarget;
    setBusy(true);
    const ok = await onSend(new FormData(element));
    setBusy(false);
    if (ok) element.reset();
  };
  const [picked, setPicked] = useState('');
  // S-332: en el celular la foto es un botón grande; se ve qué foto quedó elegida antes de enviar
  return <form className={`photo-form${big ? ' photo-form--big' : ''}`} onSubmit={submit} onReset={() => setPicked('')}>{children}<label className={`photo-field${picked ? ' has-photo' : ''}`}><Icon name="camera" size={big ? 22 : 18} /><span>{picked ? 'Foto lista' : 'Tomar foto'}</span><input type="file" name="foto_archivo" accept="image/*" capture="environment" required onChange={(event) => setPicked(event.currentTarget.files?.[0]?.name ?? '')} /></label><button className={big ? 'primary-button' : 'admin-row-button'} type="submit" disabled={busy}>{busy ? 'Subiendo…' : label}</button></form>;
}

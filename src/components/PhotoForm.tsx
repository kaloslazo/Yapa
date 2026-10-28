import { useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { Icon } from './Icon';

// foto obligatoria con la cámara del celular (S-151); la usan el panel y el reparto
export function PhotoForm({ label, onSend, children }: { label: string; onSend: (form: FormData) => Promise<boolean>; children?: ReactNode }) {
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const element = event.currentTarget;
    setBusy(true);
    const ok = await onSend(new FormData(element));
    setBusy(false);
    if (ok) element.reset();
  };
  return <form className="photo-form" onSubmit={submit}>{children}<label className="photo-field"><Icon name="camera" size={18} /><span>Foto</span><input type="file" name="foto_archivo" accept="image/*" capture="environment" required /></label><button className="admin-row-button" type="submit" disabled={busy}>{busy ? 'Subiendo…' : label}</button></form>;
}

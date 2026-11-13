import { useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { Icon } from './Icon';

// S-336: la miniatura de la foto elegida, antes de enviarla; el enlace temporal se libera al cambiarla o al salir
export function usePhotoPreview() {
  const [preview, setPreview] = useState('');
  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);
  const choose = (file: File | undefined) => setPreview(file ? URL.createObjectURL(file) : '');
  return { preview, choose, clear: () => setPreview('') };
}

export function PhotoPreview({ src }: { src: string }) {
  return src ? <div className="photo-preview"><img src={src} alt="Foto elegida" /></div> : null;
}

// foto obligatoria con la cámara del celular (S-151); la usan el panel y el reparto
export function PhotoForm({ label, onSend, children, big = false }: { label: string; onSend: (form: FormData) => Promise<boolean>; children?: ReactNode; big?: boolean }) {
  const [busy, setBusy] = useState(false);
  const { preview, choose, clear } = usePhotoPreview();
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const element = event.currentTarget;
    setBusy(true);
    const ok = await onSend(new FormData(element));
    setBusy(false);
    if (ok) element.reset();
  };
  // S-332: en el celular la foto es un botón grande; se ve qué foto quedó elegida antes de enviar
  return <form className={`photo-form${big ? ' photo-form--big' : ''}`} onSubmit={submit} onReset={clear}>{children}<PhotoPreview src={preview} /><label className={`photo-field${preview ? ' has-photo' : ''}`}><Icon name="camera" size={big ? 22 : 18} /><span>{preview ? 'Cambiar foto' : 'Tomar foto'}</span><input type="file" name="foto_archivo" accept="image/*" capture="environment" required onChange={(event) => choose(event.currentTarget.files?.[0])} /></label><button className={big ? 'primary-button' : 'admin-row-button'} type="submit" disabled={busy}>{busy ? 'Subiendo…' : label}</button></form>;
}

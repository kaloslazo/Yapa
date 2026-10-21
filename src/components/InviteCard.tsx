import { createContext, useContext, useState } from 'react';
import { Icon } from './Icon';
import { inviteShareText, whatsappShareUrl } from '../utils/invite';

export interface InviteState {
  url: string | null;
  today: number;
  total: number;
  renew: () => Promise<void>;
}

export const InviteContext = createContext<InviteState>({ url: null, today: 0, total: 0, renew: async () => {} });

// el enlace de invitación de quien está dentro (iteración 45): compartir, copiar y renovar
export function InviteBody() {
  const { url, today, total, renew } = useContext(InviteContext);
  const [copied, setCopied] = useState(false);
  const [confirming, setConfirming] = useState(false);
  if (!url) return null;
  return (
    <div className="invite-body">
      <strong>Tu enlace de invitación</strong>
      <code className="invite-link" aria-label="Tu enlace de invitación">{url}</code>
      <div className="share-actions">
        <a className="primary-button" href={whatsappShareUrl(inviteShareText(url))} target="_blank" rel="noreferrer"><Icon name="whatsapp" size={18} /> Compartir por WhatsApp</a>
        <button className="secondary-button" type="button" onClick={() => { void navigator.clipboard?.writeText(url).then(() => setCopied(true)); }}><Icon name={copied ? 'check' : 'copy'} size={16} /> {copied ? 'Copiado' : 'Copiar enlace'}</button>
      </div>
      <small>{total === 0 ? 'Quien entre con tu enlace queda en tu zona.' : `${total} ${total === 1 ? 'vecino se registró' : 'vecinos se registraron'} con tu enlace (${today} hoy).`}</small>
      {confirming
        ? <p className="invite-renew">El enlace anterior dejará de valer. <button className="auth-link" type="button" onClick={() => { setConfirming(false); setCopied(false); void renew(); }}>Sí, renovar</button> <button className="auth-link" type="button" onClick={() => setConfirming(false)}>Cancelar</button></p>
        : <button className="auth-link" type="button" onClick={() => setConfirming(true)}>Renovar enlace</button>}
    </div>
  );
}

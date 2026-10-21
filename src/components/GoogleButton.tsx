import { useEffect, useRef, useState } from 'react';
import { loadGoogle } from '../utils/google';

interface GoogleButtonProps {
  clientId: string;
  text: 'signin_with' | 'continue_with';
  onCredential: (credential: string) => void;
}

export function GoogleButton({ clientId, text, onCredential }: GoogleButtonProps) {
  const host = useRef<HTMLDivElement>(null);
  const callback = useRef(onCredential);
  const [failed, setFailed] = useState(false);
  callback.current = onCredential;

  useEffect(() => {
    let cancelled = false;
    loadGoogle().then(() => {
      const google = window.google;
      if (cancelled || !google || !host.current) return;
      google.accounts.id.initialize({ client_id: clientId, callback: (response) => callback.current(response.credential) });
      google.accounts.id.renderButton(host.current, { type: 'standard', theme: 'outline', size: 'large', shape: 'pill', text, locale: 'es', width: 280 });
    }).catch(() => { if (!cancelled) setFailed(true); });
    return () => { cancelled = true; };
  }, [clientId, text]);

  if (failed) return <p className="admin-muted">No pudimos cargar Google. Revisa tu conexión o entra con tu PIN.</p>;
  return <div className="google-button" ref={host} />;
}

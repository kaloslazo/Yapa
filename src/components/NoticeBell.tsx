import { useEffect, useRef, useState } from 'react';
import { Icon } from './Icon';
import type { Notice } from '../types';
import { badgeText, bellLabel, relativeTime } from '../utils/notices';

interface NoticeBellProps {
  notices: Notice[];
  unread: number;
  emailNotices: boolean;
  emailVerified: boolean;
  now: Date;
  onOpenNotice: (notice: Notice) => void;
  onReadAll: () => void;
  onToggleEmail: (enabled: boolean) => void;
  onVerifyEmail: () => void;
}

export function NoticeBell({ notices, unread, emailNotices, emailVerified, now, onOpenNotice, onReadAll, onToggleEmail, onVerifyEmail }: NoticeBellProps) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);
  const button = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: PointerEvent) => { if (root.current && !root.current.contains(event.target as Node)) setOpen(false); };
    const escape = (event: KeyboardEvent) => { if (event.key === 'Escape') { setOpen(false); button.current?.focus(); } };
    document.addEventListener('pointerdown', close);
    document.addEventListener('keydown', escape);
    return () => { document.removeEventListener('pointerdown', close); document.removeEventListener('keydown', escape); };
  }, [open]);

  return (
    <div className="notice-bell" ref={root}>
      <button className="notice-button" ref={button} type="button" aria-expanded={open} aria-controls="notice-panel" aria-label={bellLabel(unread)} onClick={() => setOpen((value) => !value)}>
        <Icon name="bell" size={20} />
        {unread > 0 ? <span className="notice-count" aria-hidden="true">{badgeText(unread)}</span> : null}
      </button>
      {open ? (
        <section className="notice-panel" id="notice-panel" aria-label="Avisos">
          <header className="notice-head">
            <h2>Avisos</h2>
            {unread > 0 ? <button className="text-button" type="button" onClick={onReadAll}>Marcar todo como leído</button> : null}
          </header>
          {notices.length === 0 ? <p className="notice-empty">Todavía no tienes avisos. Aquí te contamos cuando verifiquemos tu pago, llegue tu pedido o cerremos la semana.</p> : (
            <ul className="notice-list">
              {notices.map((notice) => (
                <li key={notice.id}>
                  <button className={`notice-item ${notice.read ? '' : 'is-unread'}`} type="button" onClick={() => { setOpen(false); onOpenNotice(notice); }}>
                    <strong>{notice.read ? null : <span className="sr-only">Sin leer. </span>}{notice.title}</strong>
                    <span>{notice.text}</span>
                    <time dateTime={notice.at}>{relativeTime(notice.at, now)}</time>
                  </button>
                </li>
              ))}
            </ul>
          )}
          <footer className="notice-foot">
            {emailVerified ? (
              <label className="notice-toggle"><input type="checkbox" checked={emailNotices} onChange={(event) => onToggleEmail(event.target.checked)} /> Avisarme también por correo</label>
            ) : (
              <p>Verifica tu correo para recibir también por correo los avisos de dinero y entregas. <button className="text-button" type="button" onClick={() => { setOpen(false); onVerifyEmail(); }}>Verificar mi correo</button></p>
            )}
          </footer>
        </section>
      ) : null}
    </div>
  );
}

import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Icon } from './Icon';
import type { Account } from '../types';
import { formatMoney } from '../utils/format';

export type AuthAudience = 'vecino' | 'admin';

interface AuthDialogProps {
  open: boolean;
  account: Account | null;
  initialAudience?: AuthAudience;
  onClose: () => void;
  onLogin: (kind: AuthAudience, user: string, secret: string) => Promise<Account>;
  onLogout: () => Promise<void>;
  onForgotPin: (user: string) => Promise<string>;
  onOpenAdmin: () => void;
  onOpenZone: () => void;
  onOpenOrders: () => void;
}

const ROLE_NAMES = { vecino: 'Vecino', admin_zona: 'Admin de zona', admin: 'Equipo Yapa' } as const;

export function shareText(code: string) {
  return `Hola, compro las verduras de la semana con Yapa: pagamos precio de mayorista entre vecinos y lo que ahorramos nos vuelve. Pide tu alta con mi código ${code} y los dos ganamos S/ 3 de saldo.`;
}

export function AuthDialog({ open, account, initialAudience = 'vecino', onClose, onLogin, onLogout, onForgotPin, onOpenAdmin, onOpenZone, onOpenOrders }: AuthDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [audience, setAudience] = useState<AuthAudience>(initialAudience);
  const [user, setUser] = useState('');
  const [secret, setSecret] = useState('');
  const [feedback, setFeedback] = useState('');
  const [busy, setBusy] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotMessage, setForgotMessage] = useState('');

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    if (open) {
      setAudience(initialAudience);
      setUser('');
      setSecret('');
      setFeedback('');
      setShowSignup(false);
      setShowForgot(false);
      setForgotMessage('');
    }
  }, [initialAudience, open]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback('');
    setBusy(true);
    try {
      await onLogin(audience, user.trim(), secret);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'No pudimos entrar. Inténtalo de nuevo.');
    } finally {
      setBusy(false);
    }
  };

  const forgot = async () => {
    setBusy(true);
    try {
      setForgotMessage(await onForgotPin(user.trim()));
    } catch (error) {
      setForgotMessage(error instanceof Error ? error.message : 'No pudimos enviar tu pedido. Inténtalo de nuevo.');
    } finally {
      setBusy(false);
    }
  };

  const go = (action: () => void) => { onClose(); action(); };

  return (
    <dialog ref={dialogRef} className="checkout-dialog auth-dialog" aria-labelledby="auth-title" onCancel={(event) => { event.preventDefault(); onClose(); }} onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      {account ? (
        <div className="auth-account-state">
          <div className="auth-dialog-topline"><div className="auth-brandline"><img src="/images/brand/yapa-mark.png" alt="" width="512" height="512" /><span>yapa</span></div><button className="icon-button" type="button" onClick={onClose} aria-label="Cerrar"><Icon name="close" size={20} /></button></div>
          <span className={`role-badge role-badge--${account.role}`}>{account.role === 'admin_zona' ? <Icon name="crown" size={14} /> : null}{ROLE_NAMES[account.role]}</span>
          <h2 id="auth-title">Hola, {account.name.split(' ')[0]}</h2>
          {account.role !== 'admin' ? <div className="auth-account-detail"><strong>Saldo a favor: {formatMoney(account.balance ?? 0)}</strong><span>Cliente n.º {account.user}</span></div> : <p>Tienes acceso al centro de operaciones de Yapa.</p>}
          {account.referralCode ? <div className="referral-card"><span>Tu código para invitar vecinos</span><strong>{account.referralCode}</strong><a className="secondary-button" href={`https://wa.me/?text=${encodeURIComponent(shareText(account.referralCode))}`} target="_blank" rel="noreferrer"><Icon name="whatsapp" size={17} /> Compartir por WhatsApp</a><small>Cuando tu invitado recibe su primer pedido, los dos ganan S/ 3 de saldo.</small></div> : null}
          <div className="auth-account-actions">
            {account.role === 'admin' ? <button className="primary-button" type="button" onClick={() => go(onOpenAdmin)}>Ir al centro de operaciones <Icon name="arrow" size={17} /></button> : <>
              <button className="primary-button" type="button" onClick={() => go(onOpenOrders)}>Mis pedidos <Icon name="arrow" size={17} /></button>
              <button className="secondary-button" type="button" onClick={() => go(onOpenZone)}>{account.role === 'admin_zona' ? <><Icon name="crown" size={16} /> Panel de mi zona</> : <><Icon name="map" size={16} /> Mi zona</>}</button>
            </>}
          </div>
          <button className="auth-link auth-switch-account" type="button" onClick={() => void onLogout()}><Icon name="signout" size={15} /> Salir</button>
        </div>
      ) : (
        <>
          <div className="dialog-header auth-dialog-header">
            <div><div className="auth-brandline"><img src="/images/brand/yapa-mark.png" alt="" width="512" height="512" /><span>yapa</span></div><h2 id="auth-title">{audience === 'admin' ? 'Acceso de operaciones' : 'Entra a tu cuenta'}</h2><p>{audience === 'admin' ? 'Solo para el equipo de Yapa.' : 'Con tu número de cliente y tu PIN de 6 dígitos.'}</p></div>
            <button className="icon-button" type="button" onClick={onClose} aria-label="Cerrar acceso"><Icon name="close" size={20} /></button>
          </div>
          <div className="auth-audience-switch" role="group" aria-label="Elige cómo entrar"><button className={audience === 'vecino' ? 'is-active' : ''} type="button" aria-pressed={audience === 'vecino'} onClick={() => { setAudience('vecino'); setFeedback(''); }}><Icon name="basket" size={15} />Soy vecino</button><button className={audience === 'admin' ? 'is-active' : ''} type="button" aria-pressed={audience === 'admin'} onClick={() => { setAudience('admin'); setFeedback(''); }}><Icon name="user" size={15} />Equipo Yapa</button></div>
          <form className="auth-form" onSubmit={submit}>
            <label className="auth-field"><span>{audience === 'admin' ? 'Usuario' : 'Número de cliente'}</span><input name="usuario" value={user} onChange={(event) => setUser(audience === 'admin' ? event.target.value : event.target.value.replace(/\D/g, ''))} inputMode={audience === 'admin' ? 'text' : 'numeric'} autoComplete="username" placeholder={audience === 'admin' ? 'admin-yapa' : 'Ej. 101'} required /></label>
            <label className="auth-field"><span>{audience === 'admin' ? 'Contraseña' : 'PIN'}</span><input name="secreto" type="password" value={secret} onChange={(event) => setSecret(audience === 'admin' ? event.target.value : event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode={audience === 'admin' ? 'text' : 'numeric'} autoComplete="current-password" placeholder={audience === 'admin' ? '' : '••••••'} required className={audience === 'vecino' ? 'pin-input' : ''} /></label>
            {feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null}
            <button className="primary-button" type="submit" disabled={busy} aria-busy={busy}>{busy ? 'Entrando…' : audience === 'admin' ? 'Entrar al panel' : 'Entrar a Yapa'} {!busy ? <Icon name="arrow" size={17} /> : null}</button>
          </form>
          {audience === 'vecino' ? (
            <div className="signup-help">
              <button className="auth-link" type="button" onClick={() => setShowSignup((value) => !value)} aria-expanded={showSignup}>¿Todavía no tienes cuenta?</button>
              <button className="auth-link" type="button" onClick={() => setShowForgot((value) => !value)} aria-expanded={showForgot}>¿Olvidaste tu PIN?</button>
              {showForgot ? <div className="forgot-pin"><p>Escribe tu número de cliente arriba. El equipo de Yapa te escribirá por WhatsApp, al celular que registraste, con un PIN nuevo.</p><button className="secondary-button" type="button" disabled={!user.trim() || busy} onClick={() => void forgot()}>Pedir un PIN nuevo</button>{forgotMessage ? <p className="auth-feedback" role="status">{forgotMessage}</p> : null}</div> : null}
              {showSignup ? <ol className="next-steps next-steps--compact"><li><span>1</span>Pídele al admin de tu edificio, o a Yapa por WhatsApp, que te dé de alta.</li><li><span>2</span>Si un vecino te invitó, dale su código: los dos ganan S/ 3.</li><li><span>3</span>Aceptas que Yapa guarde tu nombre y celular para tus pedidos, y te llega tu PIN.</li></ol> : null}
            </div>
          ) : null}
        </>
      )}
    </dialog>
  );
}

import { useContext, useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Icon } from './Icon';
import { GoogleButton } from './GoogleButton';
import { InviteBody, InviteContext } from './InviteCard';
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
  googleClientId: string | null;
  onGoogleLogin: (credential: string) => Promise<void>;
  onGoogleLink: (credential: string) => Promise<void>;
  onGoogleUnlink: () => Promise<void>;
  onResetPin: (user: string, code: string, pin: string) => Promise<string>;
  onSendEmail: (email: string) => Promise<void>;
  onVerifyEmail: (code: string) => Promise<void>;
  onCreatePin: (pin: string) => Promise<void>;
  onOpenAdmin: () => void;
  onOpenZone: () => void;
  onOpenOrders: () => void;
}

const ROLE_NAMES = { vecino: 'Vecino', admin_zona: 'Admin de zona', admin: 'Equipo Yapa' } as const;

export function shareText(code: string) {
  return `Hola, compro las verduras de la semana con Yapa: pagamos precio de mayorista entre vecinos y lo que ahorramos nos vuelve. Pide tu alta con mi código ${code} y los dos ganamos S/ 3 de saldo.`;
}

export function AuthDialog({ open, account, initialAudience = 'vecino', onClose, onLogin, onLogout, googleClientId, onGoogleLogin, onGoogleLink, onGoogleUnlink, onForgotPin, onResetPin, onSendEmail, onVerifyEmail, onCreatePin, onOpenAdmin, onOpenZone, onOpenOrders }: AuthDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [audience, setAudience] = useState<AuthAudience>(initialAudience);
  const [user, setUser] = useState('');
  const [secret, setSecret] = useState('');
  const [feedback, setFeedback] = useState('');
  const [busy, setBusy] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const { url: inviteUrl } = useContext(InviteContext);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotMessage, setForgotMessage] = useState('');
  const [forgotCode, setForgotCode] = useState('');
  const [forgotPin, setForgotPin] = useState('');
  const [resetMessage, setResetMessage] = useState('');
  const [emailInput, setEmailInput] = useState('');
  const [newPin, setNewPin] = useState('');
  const [pinMessage, setPinMessage] = useState('');
  const [emailCode, setEmailCode] = useState('');
  const [emailStep, setEmailStep] = useState<'ask' | 'code'>('ask');
  const [emailMessage, setEmailMessage] = useState('');
  const [googleMessage, setGoogleMessage] = useState('');

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
      setForgotCode('');
      setForgotPin('');
      setResetMessage('');
      setEmailInput('');
      setEmailCode('');
      setEmailMessage('');
      setGoogleMessage('');
      setEmailStep(account?.email ? 'code' : 'ask');
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

  const createPin = async () => {
    setBusy(true);
    try {
      await onCreatePin(newPin);
      setNewPin('');
      setPinMessage('Listo: ya puedes entrar también con tu correo o celular y tu PIN.');
    } catch (error) {
      setPinMessage(error instanceof Error ? error.message : 'No pudimos guardar tu PIN. Inténtalo de nuevo.');
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

  const resetWithCode = async () => {
    setBusy(true);
    try {
      setResetMessage(await onResetPin(user.trim(), forgotCode, forgotPin));
      setForgotCode('');
      setForgotPin('');
    } catch (error) {
      setResetMessage(error instanceof Error ? error.message : 'No pudimos cambiar tu PIN. Inténtalo de nuevo.');
    } finally {
      setBusy(false);
    }
  };

  const sendEmail = async () => {
    setBusy(true);
    try {
      await onSendEmail(emailInput.trim());
      setEmailStep('code');
      setEmailMessage('Te mandamos un código. Revisa tu correo (y la carpeta de spam).');
    } catch (error) {
      setEmailMessage(error instanceof Error ? error.message : 'No pudimos enviar el código. Inténtalo de nuevo.');
    } finally {
      setBusy(false);
    }
  };

  const verifyEmail = async () => {
    setBusy(true);
    try {
      await onVerifyEmail(emailCode);
      setEmailMessage('');
      setEmailCode('');
    } catch (error) {
      setEmailMessage(error instanceof Error ? error.message : 'No pudimos verificar el código. Inténtalo de nuevo.');
    } finally {
      setBusy(false);
    }
  };

  const googleAction = async (action: () => Promise<void>) => {
    setGoogleMessage('');
    try {
      await action();
    } catch (error) {
      setGoogleMessage(error instanceof Error ? error.message : 'No pudimos usar tu cuenta de Google. Inténtalo de nuevo.');
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
          {account.role !== 'admin' ? (account.emailVerified ? <p className="email-ok"><Icon name="ok" size={16} /> Correo verificado: {account.email}</p> : (
            <div className="email-card"><strong>Verifica tu correo</strong><p>Con tu correo verificado recuperas tu PIN tú mismo, sin esperar a nadie.</p>
              {emailStep === 'ask' ? <form onSubmit={(event) => { event.preventDefault(); void sendEmail(); }}><label className="auth-field"><span>Tu correo</span><input type="email" value={emailInput} onChange={(event) => setEmailInput(event.target.value)} autoComplete="email" placeholder="nombre@gmail.com" required /></label><button className="secondary-button" type="submit" disabled={busy || !emailInput.trim()}>Enviarme un código</button></form>
                : <form onSubmit={(event) => { event.preventDefault(); void verifyEmail(); }}><label className="auth-field"><span>Código que te llegó{account.email ? ` a ${account.email}` : ''}</span><input value={emailCode} onChange={(event) => setEmailCode(event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" placeholder="6 dígitos" /></label><button className="primary-button" type="submit" disabled={busy || emailCode.length !== 6}>Verificar</button><button className="auth-link" type="button" onClick={() => { setEmailStep('ask'); setEmailMessage(''); }}>Escribir el correo otra vez</button></form>}
              {emailMessage ? <p className="auth-feedback" role="status">{emailMessage}</p> : null}
            </div>)) : null}
          {account.role !== 'admin' && inviteUrl ? <div className="referral-card"><InviteBody /><small>Cuando tu invitado recibe su primer pedido, los dos ganan S/ 3 de saldo.</small></div> : account.referralCode ? <div className="referral-card"><span>Tu código para invitar vecinos</span><strong>{account.referralCode}</strong><a className="secondary-button" href={`https://wa.me/?text=${encodeURIComponent(shareText(account.referralCode))}`} target="_blank" rel="noreferrer"><Icon name="whatsapp" size={17} /> Compartir por WhatsApp</a><small>Cuando tu invitado recibe su primer pedido, los dos ganan S/ 3 de saldo.</small></div> : null}
          {account.role !== 'admin' && googleClientId ? (account.googleLinked
            ? <p className="email-ok"><Icon name="ok" size={16} /> Cuenta de Google vinculada <button className="auth-link" type="button" onClick={() => void googleAction(onGoogleUnlink)}>Desvincular</button></p>
            : <div className="google-link"><strong>Entra sin PIN</strong><p>Vincula tu cuenta de Google y la próxima vez entras con un toque.</p><GoogleButton clientId={googleClientId} text="continue_with" onCredential={(credential) => void googleAction(() => onGoogleLink(credential))} />{googleMessage ? <p className="auth-feedback auth-feedback--error" role="alert">{googleMessage}</p> : null}</div>) : null}
          {account.role !== 'admin' && account.hasPin === false ? <div className="email-card"><strong>Crea tu PIN (opcional)</strong><p>Hoy entras con Google. Si quieres entrar también con tu correo o celular, crea un PIN de 6 dígitos.</p><form onSubmit={(event) => { event.preventDefault(); void createPin(); }}><label className="auth-field"><span>Tu PIN nuevo</span><input type="password" className="pin-input" value={newPin} onChange={(event) => { setNewPin(event.target.value.replace(/\D/g, '').slice(0, 6)); setPinMessage(''); }} inputMode="numeric" autoComplete="new-password" placeholder="••••••" /></label><button className="secondary-button" type="submit" disabled={busy || newPin.length !== 6}>Guardar mi PIN</button></form>{pinMessage ? <p className="auth-feedback" role="status">{pinMessage}</p> : null}</div> : null}
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
            <label className="auth-field"><span>{audience === 'admin' ? 'Usuario' : 'Correo, celular o número de cliente'}</span><input name="usuario" value={user} onChange={(event) => setUser(event.target.value)} inputMode="text" autoComplete="username" autoCapitalize="none" spellCheck={false} placeholder={audience === 'admin' ? 'admin-yapa' : 'tucorreo@gmail.com o 9XXXXXXXX'} required /></label>
            <label className="auth-field"><span>{audience === 'admin' ? 'Contraseña' : 'PIN'}</span><input name="secreto" type="password" value={secret} onChange={(event) => setSecret(audience === 'admin' ? event.target.value : event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode={audience === 'admin' ? 'text' : 'numeric'} autoComplete="current-password" placeholder={audience === 'admin' ? '' : '••••••'} required className={audience === 'vecino' ? 'pin-input' : ''} /></label>
            {audience === 'vecino' && googleClientId ? <p className="auth-hint">Si te registraste con Google, entra con el botón de Google: no necesitas PIN.</p> : null}
            {feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null}
            <button className="primary-button" type="submit" disabled={busy} aria-busy={busy}>{busy ? 'Entrando…' : audience === 'admin' ? 'Entrar al panel' : 'Entrar a Yapa'} {!busy ? <Icon name="arrow" size={17} /> : null}</button>
          </form>
          {audience === 'vecino' && googleClientId ? <div className="google-login"><span className="google-divider">o</span><GoogleButton clientId={googleClientId} text="signin_with" onCredential={(credential) => void googleAction(() => onGoogleLogin(credential))} />{googleMessage ? <p className="auth-feedback auth-feedback--error" role="alert">{googleMessage}</p> : null}</div> : null}
          {audience === 'vecino' ? (
            <div className="signup-help">
              <button className="auth-link" type="button" onClick={() => setShowSignup((value) => !value)} aria-expanded={showSignup}>¿Todavía no tienes cuenta?</button>
              <button className="auth-link" type="button" onClick={() => setShowForgot((value) => !value)} aria-expanded={showForgot}>¿Olvidaste tu PIN?</button>
              {showForgot ? <div className="forgot-pin"><p>Escribe tu correo, celular o número de cliente arriba. Si verificaste tu correo, te mandamos un código ahí; si no, el equipo de Yapa te escribirá por WhatsApp al celular que registraste.</p><button className="secondary-button" type="button" disabled={!user.trim() || busy} onClick={() => void forgot()}>Pedir ayuda con mi PIN</button>{forgotMessage ? <p className="auth-feedback" role="status">{forgotMessage}</p> : null}
                <form className="forgot-code" onSubmit={(event) => { event.preventDefault(); void resetWithCode(); }}><strong>¿Ya tienes tu código?</strong>
                  <label className="auth-field"><span>Código del correo</span><input value={forgotCode} onChange={(event) => setForgotCode(event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" placeholder="6 dígitos" /></label>
                  <label className="auth-field"><span>PIN nuevo</span><input type="password" value={forgotPin} onChange={(event) => setForgotPin(event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="new-password" placeholder="6 dígitos" className="pin-input" /></label>
                  <button className="primary-button" type="submit" disabled={busy || !user.trim() || forgotCode.length !== 6 || forgotPin.length !== 6}>Cambiar mi PIN</button>
                  {resetMessage ? <p className="auth-feedback" role="status">{resetMessage}</p> : null}
                </form></div> : null}
              {showSignup ? <ol className="next-steps next-steps--compact"><li><span>1</span>Pídele a un vecino de tu zona, o al admin de tu edificio, su enlace de invitación de Yapa.</li><li><span>2</span>Ábrelo en tu celular: te registras con tu correo o con Google en un minuto.</li><li><span>3</span>Quedas en su zona y, cuando recibas tu primer pedido, los dos ganan S/ 3.</li></ol> : null}
            </div>
          ) : null}
        </>
      )}
    </dialog>
  );
}

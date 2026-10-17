import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Icon } from './Icon';
import { authMode, localDemoAdmin, loginAccount, registerAccount, requestPasswordReset, signOutAccount } from '../services/auth';
import type { AccountProfile } from '../types';
import { DEFAULT_ZONE_ID, zoneById, zones } from '../data/catalog';
import { validateAuthInput } from '../utils/domain';

type AuthMode = 'login' | 'register';
export type AuthAudience = 'user' | 'admin';

interface AuthDialogProps {
  open: boolean;
  onClose: () => void;
  onAuthenticated: (account: AccountProfile, audience: AuthAudience) => void;
  currentAccount?: AccountProfile | null;
  initialAudience?: AuthAudience;
  onSignedOut?: () => void;
  onOpenAdmin?: () => void;
}

export function AuthDialog({ open, onClose, onAuthenticated, currentAccount, initialAudience = 'user', onSignedOut, onOpenAdmin }: AuthDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [mode, setMode] = useState<AuthMode>('login');
  const [audience, setAudience] = useState<AuthAudience>(initialAudience);
  const [completed, setCompleted] = useState(false);
  const [feedback, setFeedback] = useState<{ tone: 'error' | 'notice'; message: string } | null>(null);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [zoneId, setZoneId] = useState(DEFAULT_ZONE_ID);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    if (open) {
      setAudience(initialAudience);
      setMode('login');
      setCompleted(false);
      setFeedback(null);
      setName('');
      setPhone('');
      setZoneId(DEFAULT_ZONE_ID);
      setEmail('');
      setPassword('');
    }
  }, [initialAudience, open]);

  const selectAudience = (nextAudience: AuthAudience) => {
    setAudience(nextAudience);
    setMode('login');
    setCompleted(false);
    setFeedback(null);
  };

  const selectMode = (nextMode: AuthMode) => {
    setMode(nextMode);
    setCompleted(false);
    setFeedback(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback(null);

    const formData = new FormData(event.currentTarget);
    const formName = String(formData.get('name') || name).trim();
    const formPhone = String(formData.get('phone') || phone);
    const formEmail = String(formData.get('email') || email).trim();
    const formPassword = String(formData.get('password') || password);
    const validationMessage = validateAuthInput({ mode, name: formName, phone: formPhone, email: formEmail, password: formPassword });
    if (validationMessage) {
      setFeedback({ tone: 'error', message: validationMessage });
      return;
    }

    setSubmitting(true);
    try {
      const profile = mode === 'register'
        ? await registerAccount({ name: formName, phone: formPhone.replace(/\s/g, ''), district: zoneById(zoneId)?.district ?? 'Lince', zoneId, email: formEmail, password: formPassword })
        : await loginAccount(formEmail, formPassword);

      if (audience === 'admin' && profile.role !== 'admin') {
        await signOutAccount();
        onSignedOut?.();
        throw new Error('Esta cuenta puede comprar, pero todavía no tiene permisos de administración.');
      }

      setCompleted(true);
      onAuthenticated(profile, audience);
    } catch (error) {
      setFeedback({ tone: 'error', message: error instanceof Error ? error.message : 'No pudimos completar el acceso. Inténtalo nuevamente.' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!email.trim()) {
      setFeedback({ tone: 'error', message: 'Escribe tu correo para enviarte el enlace de recuperación.' });
      return;
    }
    try {
      await requestPasswordReset(email);
      setFeedback({ tone: 'notice', message: 'Te enviamos un enlace para recuperar tu acceso.' });
    } catch (error) {
      setFeedback({ tone: 'error', message: error instanceof Error ? error.message : 'No pudimos solicitar la recuperación.' });
    }
  };

  const handleSignOut = async () => {
    setSigningOut(true);
    try {
      await signOutAccount();
      onSignedOut?.();
      setFeedback(null);
    } catch (error) {
      setFeedback({ tone: 'error', message: error instanceof Error ? error.message : 'No pudimos cerrar tu sesión.' });
    } finally {
      setSigningOut(false);
    }
  };

  const close = () => onClose();
  const activeAccountForView = currentAccount && !completed ? currentAccount : null;

  return (
    <dialog ref={dialogRef} className="checkout-dialog auth-dialog" aria-labelledby="auth-title" onCancel={(event) => { event.preventDefault(); close(); }} onClick={(event) => { if (event.target === event.currentTarget) close(); }}>
      {activeAccountForView ? (
        <div className="auth-account-state">
          <div className="auth-dialog-topline"><div className="auth-brandline"><img src="/images/brand/yapa-mark.png" alt="" width="512" height="512" /><span>yapa</span></div><button className="icon-button" type="button" onClick={close} aria-label="Cerrar cuenta"><Icon name="close" size={20} /></button></div>
          <span className="dialog-step">Sesión activa</span>
          <div className="auth-account-avatar"><Icon name="user" size={26} /></div>
                    <h2 id="auth-title">Hola, {activeAccountForView.name}</h2>
          <p>Tu cuenta ya está abierta en este dispositivo. Elige a dónde quieres ir.</p>
          <div className="auth-account-detail"><strong>{activeAccountForView.email}</strong><span>{activeAccountForView.role === 'admin' ? 'Equipo administrador' : `Compras en ${zoneById(activeAccountForView.zoneId)?.name ?? activeAccountForView.district}`}</span></div>
          <div className="auth-account-actions"><button className="primary-button" type="button" onClick={close}>Comprar como usuario <Icon name="arrow" size={17} /></button>{activeAccountForView.role === 'admin' ? <button className="secondary-button" type="button" onClick={() => { close(); onOpenAdmin?.(); }}>Ir al panel admin <Icon name="arrow" size={16} /></button> : null}</div>
          <button className="auth-link auth-switch-account" type="button" onClick={handleSignOut} disabled={signingOut}>{signingOut ? 'Cerrando sesión…' : 'Salir y usar otra cuenta'}</button>
          {feedback ? <p className={`auth-feedback auth-feedback--${feedback.tone}`} role="alert">{feedback.message}</p> : null}
        </div>
      ) : completed ? (
        <div className="auth-success">
          <div className="success-icon"><Icon name="check" size={30} /></div>
          <h2>{mode === 'register' ? 'Bienvenido a Yapa' : 'Qué bueno verte'}</h2>
          <p>{mode === 'register' ? 'Tu cuenta está lista para armar compras que rindan en Lima.' : 'Ya puedes continuar con tu canasta y elegir tu entrega.'}</p>
          <button className="primary-button" type="button" onClick={close}>Volver a comprar <Icon name="arrow" size={17} /></button>
        </div>
      ) : (
        <>
          <div className="dialog-header auth-dialog-header">
            <div><div className="auth-brandline"><img src="/images/brand/yapa-mark.png" alt="" width="512" height="512" /><span>yapa</span></div><h2 id="auth-title">{audience === 'admin' ? 'Acceso de operaciones' : 'Compra con tu cuenta'}</h2><p>{audience === 'admin' ? 'Ingresa con una cuenta autorizada para gestionar Yapa.' : 'Guarda tu zona y vuelve más rápido a tu canasta.'}</p></div>
            <button className="icon-button" type="button" onClick={close} aria-label="Cerrar acceso"><Icon name="close" size={20} /></button>
          </div>
          <div className="auth-audience-switch" role="group" aria-label="Elige cómo entrar a Yapa"><button className={audience === 'user' ? 'is-active' : ''} type="button" aria-pressed={audience === 'user'} onClick={() => selectAudience('user')}><Icon name="box" size={15} />Comprar como usuario</button><button className={audience === 'admin' ? 'is-active' : ''} type="button" aria-pressed={audience === 'admin'} onClick={() => selectAudience('admin')}><Icon name="user" size={15} />Entrar como admin</button></div>
          {audience === 'user' ? <div className="auth-switch" role="tablist" aria-label="Tipo de acceso"><button className={mode === 'login' ? 'is-active' : ''} type="button" role="tab" aria-selected={mode === 'login'} onClick={() => selectMode('login')}>Ingresar</button><button className={mode === 'register' ? 'is-active' : ''} type="button" role="tab" aria-selected={mode === 'register'} onClick={() => selectMode('register')}>Crear cuenta</button></div> : <p className="auth-access-note">Acceso protegido · solo cuentas administradoras</p>}
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            {mode === 'register' && audience === 'user' ? <><label className="auth-field"><span>¿Cómo te llamas?</span><input name="name" type="text" value={name} onChange={(event) => setName(event.target.value)} placeholder="Ej. Andrea Quispe" autoComplete="name" required /></label><div className="auth-grid"><label className="auth-field"><span>Celular</span><div className="phone-input"><strong>+51</strong><input name="phone" type="tel" inputMode="numeric" value={phone} onChange={(event) => setPhone(event.target.value.replace(/[^\d\s]/g, ''))} placeholder="987 654 321" autoComplete="tel" required /></div></label><label className="auth-field"><span>Tu zona</span><select name="zone" value={zoneId} onChange={(event) => setZoneId(event.target.value)}>{zones.map((zone) => <option key={zone.id} value={zone.id} disabled={!zone.active}>{zone.name} · {zone.district}{zone.active ? '' : ' (pronto)'}</option>)}</select></label></div></> : null}
            <label className="auth-field"><span>Correo electrónico</span><input name="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="tu@correo.com" autoComplete="email" required /></label>
            <label className="auth-field"><span>Contraseña</span><input name="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Mínimo 8 caracteres" autoComplete={mode === 'register' ? 'new-password' : 'current-password'} required /></label>
            {mode === 'login' ? <><button className="auth-link" type="button" onClick={handleForgotPassword}>¿Olvidaste tu contraseña?</button>{authMode === 'local' ? <p className="auth-hint">Demo admin local: {localDemoAdmin.email} · {localDemoAdmin.password}</p> : null}</> : <p className="auth-hint">Usaremos tu número solo para coordinar la entrega.</p>}
            {feedback ? <p className={`auth-feedback auth-feedback--${feedback.tone}`} role="alert">{feedback.message}</p> : null}
            <button className="primary-button" type="submit" disabled={submitting} aria-busy={submitting}>{audience === 'admin' ? 'Entrar al panel' : mode === 'login' ? 'Ingresar a Yapa' : 'Crear mi cuenta'}{submitting ? ' · Procesando…' : null} {!submitting ? <Icon name="arrow" size={17} /> : null}</button>
            <p className="dialog-disclaimer">Pagos simulados. Tus datos de cuenta se guardan de forma segura en Yapa.</p>
          </form>
        </>
      )}
    </dialog>
  );
}

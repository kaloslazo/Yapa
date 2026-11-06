import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { Icon, type IconName } from './Icon';
import { GoogleButton } from './GoogleButton';
import type { AuthPageId, StaffLoginKind } from '../utils/authRoutes';

export type LoginKind = 'vecino' | StaffLoginKind;

interface AuthPageProps {
  page: AuthPageId;
  initialRole?: StaffLoginKind;
  googleClientId: string | null;
  onLogin: (kind: LoginKind, user: string, secret: string) => Promise<unknown>;
  onGoogleLogin: (credential: string) => Promise<void>;
  onForgotPin: (user: string) => Promise<string>;
  onResetPin: (user: string, code: string, pin: string) => Promise<string>;
  onSwitch: (page: AuthPageId) => void;
  onBack: () => void;
}

// iteraciones 54 y 55: en el acceso del equipo entran todos los que no son vecinos, cada uno con su usuario y contraseña
const STAFF_KINDS: Array<{ id: StaffLoginKind; label: string; icon: IconName }> = [
  { id: 'admin', label: 'Administración', icon: 'gear' },
  { id: 'compras', label: 'Compras', icon: 'cart' },
  { id: 'armador', label: 'Armado', icon: 'box' },
  { id: 'atencion', label: 'Atención', icon: 'headset' },
  { id: 'porteria', label: 'Portería', icon: 'building' },
  { id: 'transportista', label: 'Reparto', icon: 'truck' },
  { id: 'proveedor', label: 'Proveedor', icon: 'store' },
];

export const LOGIN_HINT = 'Con tu correo, celular o número de cliente y tu PIN de 6 dígitos.';

// seis casillas a la vista; un solo input real debajo para teclado numérico, gestores de claves y pegar
function PinField({ label, name, value, onChange }: { label: string; name: string; value: string; onChange: (pin: string) => void }) {
  return (
    <label className="auth-field pin-field"><span>{label}</span>
      <span className="pin-cells">
        <input name={name} type="password" value={value} onChange={(event) => onChange(event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" pattern="[0-9]*" maxLength={6} autoComplete="current-password" required aria-describedby={`${name}-ayuda`} />
        {Array.from({ length: 6 }, (_, index) => <span key={index} className={`pin-cell ${index < value.length ? 'is-filled' : ''} ${index === Math.min(value.length, 5) ? 'is-next' : ''}`} aria-hidden="true" />)}
      </span>
      <small id={`${name}-ayuda`} className="sr-only">6 dígitos</small>
    </label>
  );
}

export function AuthPage({ page, initialRole = 'admin', googleClientId, onLogin, onGoogleLogin, onForgotPin, onResetPin, onSwitch, onBack }: AuthPageProps) {
  const titleRef = useRef<HTMLHeadingElement>(null);
  const staff = page === 'equipo';
  const [staffKind, setStaffKind] = useState<StaffLoginKind>(initialRole);
  const [user, setUser] = useState('');
  const [secret, setSecret] = useState('');
  const [feedback, setFeedback] = useState('');
  const [busy, setBusy] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotMessage, setForgotMessage] = useState('');
  const [forgotCode, setForgotCode] = useState('');
  const [forgotPin, setForgotPin] = useState('');
  const [resetMessage, setResetMessage] = useState('');
  const [googleMessage, setGoogleMessage] = useState('');

  useEffect(() => {
    const title = document.title;
    return () => { document.title = title; };
  }, []);

  useEffect(() => {
    setStaffKind(initialRole);
    setUser('');
    setSecret('');
    setFeedback('');
    setShowSignup(false);
    setShowForgot(false);
    document.title = staff ? 'Acceso del equipo · Yapa' : 'Entrar · Yapa';
    window.scrollTo({ top: 0 });
    titleRef.current?.focus();
  }, [page, initialRole, staff]);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback('');
    setBusy(true);
    try {
      await onLogin(staff ? staffKind : 'vecino', user.trim(), secret);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'No pudimos entrar. Inténtalo de nuevo.');
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

  const googleLogin = async (credential: string) => {
    setGoogleMessage('');
    try {
      await onGoogleLogin(credential);
    } catch (error) {
      setGoogleMessage(error instanceof Error ? error.message : 'No pudimos usar tu cuenta de Google. Inténtalo de nuevo.');
    }
  };

  return (
    <main className={`auth-page ${staff ? 'auth-page--staff' : ''}`}>
      <aside className="auth-aside" aria-hidden="true">
        <div className="auth-brandline"><img src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" /><span>yapa</span></div>
        <p className="auth-aside-title">{staff ? 'Cada semana, el mercado llega a cada edificio gracias a ti.' : 'Lo que ahorramos entre vecinos vuelve a tu saldo.'}</p>
        <img className="auth-aside-art" src="/images/brand/yapa-farmer-banner.webp" alt="" width="760" height="694" />
      </aside>
      <div className="auth-main">
        <div className="auth-topbar">
          <a className="auth-brandline auth-brandline--login" href="/" onClick={(event) => { event.preventDefault(); onBack(); }} aria-label="Yapa, volver a la tienda"><img src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" /><span>yapa</span></a>
          <button className="auth-back" type="button" onClick={onBack}><Icon name="arrow" size={16} /> Volver a la tienda</button>
        </div>
        <div className="auth-body">
          <h1 id="auth-title" ref={titleRef} tabIndex={-1}>{staff ? 'Acceso del equipo' : 'Entra a Yapa'}</h1>
          <p className="auth-lead">{staff ? 'Para el equipo de Yapa, las porterías, el reparto y los proveedores aliados. Elige tu rol.' : LOGIN_HINT}</p>
          <form className="auth-form" onSubmit={submit}>
            {staff ? <fieldset className="staff-kinds"><legend>Entro como</legend>{STAFF_KINDS.map((kind) => <label key={kind.id} className={`staff-kind ${staffKind === kind.id ? 'is-selected' : ''}`}><input type="radio" name="tipo" value={kind.id} checked={staffKind === kind.id} onChange={() => { setStaffKind(kind.id); setFeedback(''); }} /><Icon name={kind.icon} size={20} /><span>{kind.label}</span></label>)}</fieldset> : null}
            <label className="auth-field"><span>{staff ? 'Usuario' : 'Correo, celular o n.º de cliente'}</span><input name="usuario" value={user} onChange={(event) => setUser(event.target.value)} inputMode="text" autoComplete="username" autoCapitalize="none" spellCheck={false} placeholder={staff ? 'tu usuario' : 'tucorreo@gmail.com o 9XXXXXXXX'} required /></label>
            {staff
              ? <label className="auth-field"><span>Contraseña</span><input name="secreto" type="password" value={secret} onChange={(event) => setSecret(event.target.value)} autoComplete="current-password" required /></label>
              : <PinField label="PIN" name="secreto" value={secret} onChange={setSecret} />}
            {feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null}
            <button className="primary-button" type="submit" disabled={busy} aria-busy={busy}>{busy ? 'Entrando…' : 'Entrar'}</button>
          </form>
          {!staff && googleClientId ? <div className="google-login"><span className="google-divider">o entra con</span><GoogleButton clientId={googleClientId} text="signin_with" onCredential={(credential) => void googleLogin(credential)} /><p className="auth-hint">Si te registraste con Google, no necesitas PIN.</p>{googleMessage ? <p className="auth-feedback auth-feedback--error" role="alert">{googleMessage}</p> : null}</div> : null}
          {!staff ? (
            <div className="signup-help">
              <div className="auth-links"><button className="auth-link" type="button" onClick={() => { setShowForgot((value) => !value); setShowSignup(false); }} aria-expanded={showForgot}>Olvidé mi PIN</button><button className="auth-link" type="button" onClick={() => { setShowSignup((value) => !value); setShowForgot(false); }} aria-expanded={showSignup}>No tengo cuenta</button></div>
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
        </div>
        <a className="auth-link auth-audience-link" href={staff ? '/entrar' : '/equipo'} onClick={(event) => { event.preventDefault(); onSwitch(staff ? 'entrar' : 'equipo'); }}>{staff ? '← Volver al ingreso de vecinos' : '¿Eres del equipo, portería, reparto o proveedor? Entra aquí'}</a>
      </div>
    </main>
  );
}

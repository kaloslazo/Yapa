import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from '../services/api';
import { decodeGoogleProfile, isValidPhone, isWeakPin, type GoogleProfile } from '../utils/invite';
import { GoogleButton } from './GoogleButton';
import { Icon } from './Icon';

type Raw = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

interface Preview { zona: string; distrito: string; invita: string; vecinos: number; minimo_grupo: number }
type Step = 'method' | 'google' | 'email' | 'code';

interface InvitePageProps {
  code: string;
  googleClientId: string | null;
  signedIn: boolean;
  onJoined: (me: Raw) => void;
  onGoHome: () => void;
}

const messageOf = (error: unknown) => (error instanceof Error ? error.message : 'Algo salió mal. Inténtalo de nuevo.');

// página a la que llega quien abre el enlace de un vecino: /unete/<código>
export function InvitePage({ code, googleClientId, signedIn, onJoined, onGoHome }: InvitePageProps) {
  const [preview, setPreview] = useState<Preview | null>(null);
  const [broken, setBroken] = useState('');
  const [step, setStep] = useState<Step>('method');
  const [phone, setPhone] = useState('');
  const [consent, setConsent] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [credential, setCredential] = useState('');
  const [profile, setProfile] = useState<GoogleProfile | null>(null);
  const [codeInput, setCodeInput] = useState('');
  const [pin, setPin] = useState('');
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [notice, setNotice] = useState('');
  const card = useRef<HTMLElement>(null);

  useEffect(() => {
    api.get<Preview>(`/api/invitaciones/${code}`).then(setPreview).catch((error) => setBroken(error instanceof ApiError && error.status === 0 ? messageOf(error) : 'Este enlace no existe o ya no vale. Pídele a tu vecino que te mande uno nuevo.'));
  }, [code]);

  useEffect(() => { document.title = preview ? `${preview.invita} te invita a Yapa` : 'Yapa · Invitación'; }, [preview]);

  // al cambiar de paso, el cursor va al primer campo que se puede escribir (también para quien usa lector de pantalla)
  useEffect(() => {
    if (step !== 'method') card.current?.querySelector<HTMLInputElement>('input:not([readonly]):not([type=checkbox])')?.focus();
  }, [step]);

  // al escribir se limpia el aviso de error anterior
  const typed = (setter: (value: string) => void, clean: (value: string) => string = (value) => value) => (event: { target: { value: string } }) => { setter(clean(event.target.value)); setFeedback(''); };

  const common = (): string => {
    if (!isValidPhone(phone)) return 'Escribe tu celular: 9 dígitos y empieza con 9.';
    if (!consent) return 'Para registrarte tienes que aceptar que Yapa guarde tus datos.';
    return '';
  };

  const run = async (action: () => Promise<Raw | void>) => {
    setBusy(true);
    setFeedback('');
    try {
      const result = await action();
      if (result) onJoined(result);
    } catch (error) {
      setFeedback(messageOf(error));
    } finally {
      setBusy(false);
    }
  };

  const googleChosen = (token: string) => {
    const found = decodeGoogleProfile(token);
    if (!found) { setFeedback('No pudimos leer tu cuenta de Google. Inténtalo de nuevo.'); return; }
    setCredential(token);
    setProfile(found);
    setFeedback('');
    setStep('google');
  };

  const createWithGoogle = () => {
    const problem = common();
    if (problem) { setFeedback(problem); return; }
    void run(() => api.post<Raw>(`/api/invitaciones/${code}/google`, { credential, celular: phone, consentimiento: consent }));
  };

  const sendCode = () => {
    const problem = (name.trim() ? '' : 'Escribe tu nombre.') || (/\S+@\S+\.\S+/.test(email) ? '' : 'Escribe un correo válido.') || common();
    if (problem) { setFeedback(problem); return; }
    void run(async () => {
      await api.post(`/api/invitaciones/${code}/correo`, { nombre: name.trim(), celular: phone, correo: email.trim(), consentimiento: consent });
      setStep('code');
      setNotice('Te mandamos un código. Revisa tu correo (y la carpeta de spam).');
    });
  };

  const confirm = () => {
    if (isWeakPin(pin)) { setFeedback('Elige un PIN de 6 dígitos que no sea muy fácil (nada de 123456 ni 111111).'); return; }
    void run(() => api.post<Raw>(`/api/invitaciones/${code}/confirmar`, { correo: email.trim(), codigo: codeInput, pin }));
  };

  const back = (to: Step) => { setStep(to); setFeedback(''); setNotice(''); };

  const phoneAndConsent = (
    <>
      <label className="auth-field"><span>Tu celular</span><input value={phone} onChange={typed(setPhone, (value) => value.replace(/\D/g, '').slice(0, 9))} inputMode="numeric" autoComplete="tel-national" placeholder="9 dígitos, empieza con 9" /></label>
      <label className="invite-consent"><input type="checkbox" checked={consent} onChange={(event) => { setConsent(event.target.checked); setFeedback(''); }} /> <span>Acepto que Yapa guarde mi nombre, correo y celular para mis pedidos. <a href="/privacidad" target="_blank" rel="noreferrer">Cómo cuidamos tus datos</a></span></label>
    </>
  );
  const errorBox = feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null;

  return (
    <main className="invite-page">
      <section className="invite-card" ref={card}>
        <div className="auth-brandline"><img src="/images/brand/yapa-mark.webp" alt="" width="192" height="192" /><span>yapa</span></div>
        {broken ? (
          <><h1>Este enlace no sirve</h1><p>{broken}</p><button className="secondary-button" type="button" onClick={onGoHome}>Ir a Yapa</button></>
        ) : !preview ? <p role="status">Abriendo tu invitación…</p> : signedIn ? (
          <><h1>Ya tienes tu cuenta</h1><p>Entraste a Yapa con tu cuenta. Si quieres invitar a otro vecino, comparte tu propio enlace desde Mi zona.</p><button className="primary-button" type="button" onClick={onGoHome}>Ir a Yapa <Icon name="arrow" size={17} /></button></>
        ) : (
          <>
            <span className="invite-chip"><Icon name="gift" size={14} /> Invitación de {preview.invita}</span>
            <h1>{preview.invita} te invita a comprar con su zona</h1>
            <p className="invite-zone"><Icon name="pin" size={16} /> {preview.zona} · {preview.distrito}</p>
            <p>{preview.vecinos > 1 ? `Ya hay ${preview.vecinos} vecinos` : 'Ya hay 1 vecino'} en esta zona. Compramos juntos el mercado de la semana, pagamos precio de mayorista y lo que ahorramos te vuelve como saldo. Con {preview.minimo_grupo} pedidos verificados, el camión llega el sábado.</p>

            {step === 'method' ? (
              <div className="invite-methods">
                <h2>Crea tu cuenta</h2>
                {googleClientId ? <GoogleButton clientId={googleClientId} text="continue_with" onCredential={googleChosen} /> : null}
                {googleClientId ? <span className="google-divider">o</span> : null}
                <button className="secondary-button invite-email-button" type="button" onClick={() => back('email')}>Registrarme con mi correo</button>
                {errorBox}
              </div>
            ) : null}

            {step === 'google' && profile ? (
              <form className="auth-form" onSubmit={(event) => { event.preventDefault(); createWithGoogle(); }}>
                <p className="invite-identity"><span className="invite-avatar" aria-hidden="true">{profile.name.slice(0, 1).toUpperCase()}</span><span>Continúas con tu cuenta de Google</span></p>
                <label className="auth-field"><span>Tu nombre</span><input value={profile.name} readOnly aria-readonly="true" className="is-readonly" /></label>
                <label className="auth-field"><span>Tu correo</span><input value={profile.email} readOnly aria-readonly="true" className="is-readonly" /></label>
                {phoneAndConsent}
                {errorBox}
                <button className="primary-button" type="submit" disabled={busy} aria-busy={busy}>{busy ? 'Creando tu cuenta…' : 'Crear mi cuenta'}</button>
                <button className="auth-link" type="button" onClick={() => { setProfile(null); setCredential(''); back('method'); }}>Usar otra cuenta de Google</button>
              </form>
            ) : null}

            {step === 'email' ? (
              <form className="auth-form" onSubmit={(event) => { event.preventDefault(); sendCode(); }}>
                <label className="auth-field"><span>Tu nombre</span><input value={name} onChange={typed(setName)} autoComplete="name" /></label>
                <label className="auth-field"><span>Tu correo</span><input type="email" value={email} onChange={typed(setEmail)} autoComplete="email" /></label>
                {phoneAndConsent}
                {errorBox}
                <button className="primary-button" type="submit" disabled={busy} aria-busy={busy}>{busy ? 'Enviando…' : 'Enviarme el código'}</button>
                <button className="auth-link" type="button" onClick={() => back('method')}>Volver</button>
              </form>
            ) : null}

            {step === 'code' ? (
              <form className="auth-form" onSubmit={(event) => { event.preventDefault(); confirm(); }}>
                <label className="auth-field"><span>Código que te llegó a {email}</span><input value={codeInput} onChange={typed(setCodeInput, (value) => value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" placeholder="6 dígitos" /></label>
                <label className="auth-field"><span>Elige tu PIN (6 dígitos)</span><input type="password" className="pin-input" value={pin} onChange={typed(setPin, (value) => value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="new-password" placeholder="••••••" /></label>
                {notice ? <p className="auth-feedback auth-feedback--notice" role="status">{notice}</p> : null}
                {errorBox}
                <button className="primary-button" type="submit" disabled={busy || codeInput.length !== 6 || pin.length !== 6} aria-busy={busy}>{busy ? 'Creando tu cuenta…' : 'Crear mi cuenta'}</button>
                <button className="auth-link" type="button" onClick={() => back('email')}>Cambiar mis datos</button>
              </form>
            ) : null}
          </>
        )}
      </section>
    </main>
  );
}

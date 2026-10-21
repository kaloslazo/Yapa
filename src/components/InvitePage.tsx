import { useEffect, useState } from 'react';
import { api, ApiError } from '../services/api';
import { isValidPhone, isWeakPin } from '../utils/invite';
import { GoogleButton } from './GoogleButton';
import { Icon } from './Icon';

type Raw = Record<string, any>; // eslint-disable-line @typescript-eslint/no-explicit-any

interface Preview { zona: string; distrito: string; invita: string; vecinos: number; minimo_grupo: number }

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
  const [phone, setPhone] = useState('');
  const [consent, setConsent] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [step, setStep] = useState<'data' | 'code'>('data');
  const [codeInput, setCodeInput] = useState('');
  const [pin, setPin] = useState('');
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    api.get<Preview>(`/api/invitaciones/${code}`).then(setPreview).catch((error) => setBroken(error instanceof ApiError && error.status === 0 ? messageOf(error) : 'Este enlace no existe o ya no vale. Pídele a tu vecino que te mande uno nuevo.'));
  }, [code]);

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

  const sendCode = () => {
    const problem = common() || (name.trim() ? '' : 'Escribe tu nombre.') || (/\S+@\S+\.\S+/.test(email) ? '' : 'Escribe un correo válido.');
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

  const withGoogle = (credential: string) => {
    const problem = common();
    if (problem) { setFeedback(problem); return; }
    void run(() => api.post<Raw>(`/api/invitaciones/${code}/google`, { credential, celular: phone, consentimiento: consent }));
  };

  return (
    <main className="invite-page">
      <section className="invite-card">
        <div className="auth-brandline"><img src="/images/brand/yapa-mark.png" alt="" width="512" height="512" /><span>yapa</span></div>
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
            {step === 'data' ? (
              <form className="auth-form" onSubmit={(event) => { event.preventDefault(); sendCode(); }}>
                <label className="auth-field"><span>Tu celular</span><input value={phone} onChange={(event) => setPhone(event.target.value.replace(/\D/g, '').slice(0, 9))} inputMode="numeric" autoComplete="tel-national" placeholder="9 dígitos" /></label>
                <label className="invite-consent"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} /> <span>Acepto que Yapa guarde mi nombre, correo y celular para mis pedidos.</span></label>
                {googleClientId ? <div className="google-login"><GoogleButton clientId={googleClientId} text="continue_with" onCredential={withGoogle} /><span className="google-divider">o con tu correo</span></div> : null}
                <label className="auth-field"><span>Tu nombre</span><input value={name} onChange={(event) => setName(event.target.value)} autoComplete="name" /></label>
                <label className="auth-field"><span>Tu correo</span><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" /></label>
                {feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null}
                <button className="primary-button" type="submit" disabled={busy} aria-busy={busy}>{busy ? 'Enviando…' : 'Enviarme el código'}</button>
              </form>
            ) : (
              <form className="auth-form" onSubmit={(event) => { event.preventDefault(); confirm(); }}>
                <label className="auth-field"><span>Código que te llegó a {email}</span><input value={codeInput} onChange={(event) => setCodeInput(event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" placeholder="6 dígitos" /></label>
                <label className="auth-field"><span>Elige tu PIN (6 dígitos)</span><input type="password" className="pin-input" value={pin} onChange={(event) => setPin(event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="new-password" placeholder="••••••" /></label>
                {notice ? <p className="auth-feedback auth-feedback--notice" role="status">{notice}</p> : null}
                {feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null}
                <button className="primary-button" type="submit" disabled={busy || codeInput.length !== 6 || pin.length !== 6} aria-busy={busy}>{busy ? 'Creando tu cuenta…' : 'Crear mi cuenta'}</button>
                <button className="auth-link" type="button" onClick={() => { setStep('data'); setFeedback(''); setNotice(''); }}>Cambiar mis datos</button>
              </form>
            )}
          </>
        )}
      </section>
    </main>
  );
}

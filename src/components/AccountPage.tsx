import { useContext, useState } from 'react';
import { Icon } from './Icon';
import { GoogleButton } from './GoogleButton';
import { InviteBody, InviteContext } from './InviteCard';
import type { Account } from '../types';
import { formatMoney } from '../utils/format';
import { ROLE_LABELS } from '../utils/roles';

interface AccountPageProps {
  account: Account;
  googleClientId: string | null;
  onGoogleLink: (credential: string) => Promise<void>;
  onGoogleUnlink: () => Promise<void>;
  onSendEmail: (email: string) => Promise<void>;
  onVerifyEmail: (code: string) => Promise<void>;
  onCreatePin: (pin: string) => Promise<void>;
  onWithdraw: (confirmation: string) => Promise<void>; // iteración 57, Ley 29733
  onLogout: () => Promise<void>;
  onOpenAdmin: () => void;
  onOpenZone: () => void;
  onOpenOrders: () => void;
}

export function shareText(code: string) {
  return `Hola, compro las verduras de la semana con Yapa: pagamos precio de mayorista entre vecinos y lo que ahorramos nos vuelve. Pide tu alta con mi código ${code} y los dos ganamos S/ 3 de saldo.`;
}

// la cuenta del vecino: antes vivía en el mismo modal que el ingreso; ahora es una vista más, como Mis pedidos
export function AccountPage({ account, googleClientId, onGoogleLink, onGoogleUnlink, onSendEmail, onVerifyEmail, onCreatePin, onWithdraw, onLogout, onOpenAdmin, onOpenZone, onOpenOrders }: AccountPageProps) {
  const { url: inviteUrl } = useContext(InviteContext);
  const [busy, setBusy] = useState(false);
  const [emailInput, setEmailInput] = useState('');
  const [emailCode, setEmailCode] = useState('');
  const [emailStep, setEmailStep] = useState<'ask' | 'code'>(account.email ? 'code' : 'ask');
  const [emailMessage, setEmailMessage] = useState('');
  const [newPin, setNewPin] = useState('');
  const [pinMessage, setPinMessage] = useState('');
  const [googleMessage, setGoogleMessage] = useState('');
  const [withdrawWord, setWithdrawWord] = useState('');
  const [withdrawMessage, setWithdrawMessage] = useState('');
  const neighbor = account.role !== 'admin';

  const run = async (action: () => Promise<void>, onError: (message: string) => void, fallback: string) => {
    setBusy(true);
    try {
      await action();
    } catch (error) {
      onError(error instanceof Error ? error.message : fallback);
    } finally {
      setBusy(false);
    }
  };

  const sendEmail = () => run(async () => {
    await onSendEmail(emailInput.trim());
    setEmailStep('code');
    setEmailMessage('Te mandamos un código. Revisa tu correo (y la carpeta de spam).');
  }, setEmailMessage, 'No pudimos enviar el código. Inténtalo de nuevo.');

  const verifyEmail = () => run(async () => {
    await onVerifyEmail(emailCode);
    setEmailMessage('');
    setEmailCode('');
  }, setEmailMessage, 'No pudimos verificar el código. Inténtalo de nuevo.');

  const createPin = () => run(async () => {
    await onCreatePin(newPin);
    setNewPin('');
    setPinMessage('Listo: ya puedes entrar también con tu correo o celular y tu PIN.');
  }, setPinMessage, 'No pudimos guardar tu PIN. Inténtalo de nuevo.');

  const googleAction = (action: () => Promise<void>) => {
    setGoogleMessage('');
    return run(action, setGoogleMessage, 'No pudimos usar tu cuenta de Google. Inténtalo de nuevo.');
  };

  return (
    <main className="customer-page account-page" id="account-page">
      <header className="customer-page-header">
        <div>
          <span className={`role-badge role-badge--${account.role}`}>{account.role === 'admin_zona' ? <Icon name="crown" size={14} /> : null}{ROLE_LABELS[account.role]}</span>
          <h1>Hola, {account.name.split(' ')[0]}</h1>
          <p>{neighbor ? `Cliente n.º ${account.user}. Aquí ves tu saldo y cómo entras a Yapa.` : 'Tienes acceso al centro de operaciones de Yapa.'}</p>
        </div>
        {neighbor ? <div className="hero-stats"><div className="customer-page-note"><span className="customer-page-note-icon"><Icon name="wallet" size={20} /></span><span><small>Tu saldo a favor</small><strong>{formatMoney(account.balance ?? 0)}</strong></span></div></div> : null}
      </header>

      <div className="account-grid">
        <section className="account-card" aria-labelledby="account-actions-title">
          <h2 id="account-actions-title">Ir a</h2>
          <div className="auth-account-actions">
            {neighbor ? <>
              <button className="primary-button" type="button" onClick={onOpenOrders}>Mis pedidos <Icon name="arrow" size={17} /></button>
              <button className="secondary-button" type="button" onClick={onOpenZone}>{account.role === 'admin_zona' ? <><Icon name="crown" size={16} /> Panel de mi zona</> : <><Icon name="map" size={16} /> Mi zona</>}</button>
            </> : <button className="primary-button" type="button" onClick={onOpenAdmin}>Ir al centro de operaciones <Icon name="arrow" size={17} /></button>}
          </div>
        </section>

        {neighbor ? (
          <section className="account-card" aria-labelledby="account-email-title">
            <h2 id="account-email-title">Tu correo</h2>
            {account.emailVerified ? <p className="email-ok"><Icon name="ok" size={16} /> Correo verificado: {account.email}</p> : <>
              <p>Con tu correo verificado recuperas tu PIN tú mismo, sin esperar a nadie.</p>
              {emailStep === 'ask'
                ? <form onSubmit={(event) => { event.preventDefault(); void sendEmail(); }}><label className="auth-field"><span>Tu correo</span><input type="email" value={emailInput} onChange={(event) => setEmailInput(event.target.value)} autoComplete="email" placeholder="nombre@gmail.com" required /></label><button className="secondary-button" type="submit" disabled={busy || !emailInput.trim()}>Enviarme un código</button></form>
                : <form onSubmit={(event) => { event.preventDefault(); void verifyEmail(); }}><label className="auth-field"><span>Código que te llegó{account.email ? ` a ${account.email}` : ''}</span><input value={emailCode} onChange={(event) => setEmailCode(event.target.value.replace(/\D/g, '').slice(0, 6))} inputMode="numeric" autoComplete="one-time-code" placeholder="6 dígitos" /></label><button className="primary-button" type="submit" disabled={busy || emailCode.length !== 6}>Verificar</button><button className="auth-link" type="button" onClick={() => { setEmailStep('ask'); setEmailMessage(''); }}>Escribir el correo otra vez</button></form>}
              {emailMessage ? <p className="auth-feedback" role="status">{emailMessage}</p> : null}
            </>}
          </section>
        ) : null}

        {neighbor && googleClientId ? (
          <section className="account-card" aria-labelledby="account-google-title">
            <h2 id="account-google-title">Entra sin PIN</h2>
            {account.googleLinked
              ? <p className="email-ok"><Icon name="ok" size={16} /> Cuenta de Google vinculada <button className="auth-link" type="button" onClick={() => void googleAction(onGoogleUnlink)}>Desvincular</button></p>
              : <><p>Vincula tu cuenta de Google y la próxima vez entras con un toque.</p><GoogleButton clientId={googleClientId} text="continue_with" onCredential={(credential) => void googleAction(() => onGoogleLink(credential))} /></>}
            {googleMessage ? <p className="auth-feedback auth-feedback--error" role="alert">{googleMessage}</p> : null}
          </section>
        ) : null}

        {neighbor && account.hasPin === false ? (
          <section className="account-card" aria-labelledby="account-pin-title">
            <h2 id="account-pin-title">Crea tu PIN (opcional)</h2>
            <p>Hoy entras con Google. Si quieres entrar también con tu correo o celular, crea un PIN de 6 dígitos.</p>
            <form onSubmit={(event) => { event.preventDefault(); void createPin(); }}><label className="auth-field"><span>Tu PIN nuevo</span><input type="password" className="pin-input" value={newPin} onChange={(event) => { setNewPin(event.target.value.replace(/\D/g, '').slice(0, 6)); setPinMessage(''); }} inputMode="numeric" autoComplete="new-password" placeholder="••••••" /></label><button className="secondary-button" type="submit" disabled={busy || newPin.length !== 6}>Guardar mi PIN</button></form>
            {pinMessage ? <p className="auth-feedback" role="status">{pinMessage}</p> : null}
          </section>
        ) : null}

        {neighbor && inviteUrl ? <section className="account-card referral-card"><InviteBody /><small>Cuando tu invitado recibe su primer pedido, los dos ganan S/ 3 de saldo.</small></section>
          : account.referralCode ? <section className="account-card referral-card"><span>Tu código para invitar vecinos</span><strong>{account.referralCode}</strong><a className="secondary-button" href={`https://wa.me/?text=${encodeURIComponent(shareText(account.referralCode))}`} target="_blank" rel="noreferrer"><Icon name="whatsapp" size={17} /> Compartir por WhatsApp</a><small>Cuando tu invitado recibe su primer pedido, los dos ganan S/ 3 de saldo.</small></section> : null}
      </div>

      {neighbor ? (
        <details className="account-card account-withdraw">
          <summary>Retirar mi consentimiento y cerrar mi cuenta</summary>
          <p>Borramos tu nombre, celular, correo, ubicación y tu cuenta de Google. Tus pedidos y pagos quedan guardados sin tus datos, porque la ley nos pide conservarlos. Antes debes tener tu saldo en cero, sin pedidos por liquidar ni reclamos pendientes.</p>
          <form onSubmit={(event) => { event.preventDefault(); void run(() => onWithdraw(withdrawWord), setWithdrawMessage, 'No pudimos cerrar tu cuenta. Inténtalo de nuevo.'); }}>
            <label className="auth-field"><span>Escribe RETIRAR para confirmar</span><input value={withdrawWord} onChange={(event) => { setWithdrawWord(event.target.value); setWithdrawMessage(''); }} autoComplete="off" spellCheck={false} /></label>
            <button className="secondary-button" type="submit" disabled={busy || withdrawWord !== 'RETIRAR'}>Cerrar mi cuenta</button>
          </form>
          {withdrawMessage ? <p className="auth-feedback auth-feedback--error" role="alert">{withdrawMessage}</p> : null}
        </details>
      ) : null}

      <button className="auth-link auth-switch-account" type="button" onClick={() => void onLogout()}><Icon name="signout" size={15} /> Salir de mi cuenta</button>
    </main>
  );
}

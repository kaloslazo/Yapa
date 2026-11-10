import { useState } from 'react';
import type { FormEvent } from 'react';
import type { Order, Quote, Zone } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';

interface PayPageProps {
  quote: Quote | null;
  zone: Zone | undefined;
  delivery: string;
  cycleOpen: boolean;
  confirmation: Order | null;
  onSubmit: (method: 'YAPE' | 'PLIN', useBalance: boolean) => Promise<void>;
  onBack: () => void;
  onOpenOrders: () => void;
  onKeepShopping: () => void;
}

const methodName = (method: string) => (method === 'PLIN' ? 'Plin' : 'Yape');
const RECEIVES: Record<string, string> = { PORTERIA: 'la recibe la portería', ENCARGADO: 'la recibe el encargado del edificio', ADMIN: 'la recibe el admin de tu zona' };

// pago en un solo paso (antes era una ventana): dónde llega, cómo pagas y cuánto; FE-04: Yapa da el código de pago al confirmar (S-150)
export function PayPage({ quote, zone, delivery, cycleOpen, confirmation, onSubmit, onBack, onOpenOrders, onKeepShopping }: PayPageProps) {
  const [method, setMethod] = useState<'YAPE' | 'PLIN'>('YAPE');
  const [useBalance, setUseBalance] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [copied, setCopied] = useState(false);

  if (confirmation) {
    const copyCode = async () => {
      try { await navigator.clipboard.writeText(confirmation.paymentCode); setCopied(true); } catch { setCopied(false); }
    };
    return (
      <main className="page-content pay-view">
        <section className="pay-done" aria-labelledby="pay-done-title">
          <span className="pay-done-icon" aria-hidden="true"><Icon name="check" size={30} weight="bold" /></span>
          <small>Pedido {confirmation.id} registrado</small>
          <h1 id="pay-done-title">Tu canasta ya está separada</h1>
          {confirmation.toPay > 0 ? (
            <div className="pay-code-card">
              <span>Yapea ahora</span>
              <strong className="pay-amount">{formatMoney(confirmation.toPay)}</strong>
              {confirmation.payTo ? <span>al Plin <b>{confirmation.payTo.number}</b> · {confirmation.payTo.holder}. También puedes pagarlo desde Yape.</span> : null}
              <span>desde tu {methodName(confirmation.method)} y escribe este código en el mensaje:</span>
              <button className="pay-code" type="button" onClick={() => void copyCode()} aria-label={`Copiar el código ${confirmation.paymentCode}`}>{confirmation.paymentCode}<Icon name={copied ? 'check' : 'copy'} size={18} /></button>
              <small>{copied ? 'Copiado' : 'Toca el código para copiarlo'} · con él verificamos tu pago</small>
            </div>
          ) : <p className="minimum-card is-ready"><Icon name="wallet" size={18} /> Tu saldo cubrió todo: <b>no tienes que yapear</b>.</p>}
          <ol className="pay-next">
            <li><b>Verificamos tu pago</b><small>hoy</small></li>
            <li><b>Compramos al por mayor</b><small>jueves</small></li>
            <li><b>Armamos tu bolsa y la llevamos a tu portería</b><small>{delivery}</small></li>
            <li><b>Si el precio bajó, te devolvemos la diferencia</b><small>al liquidar</small></li>
          </ol>
          <div className="pay-done-actions"><button className="primary-button" type="button" onClick={onOpenOrders}>Ver mis pedidos</button><button className="secondary-button" type="button" onClick={onKeepShopping}>Seguir comprando</button></div>
        </section>
      </main>
    );
  }

  if (!quote) {
    return (
      <main className="page-content pay-view">
        <div className="page-bar"><button className="round-button" type="button" onClick={onBack} aria-label="Volver a la canasta"><Icon name="back" size={20} /></button><h1>Confirmar pedido</h1><span className="round-button is-ghost" aria-hidden="true" /></div>
        <div className="shop-empty"><h3>Tu pedido todavía no está listo</h3><p>Revisa tu canasta y toca «Ir a pagar» para preparar el pedido.</p><button className="primary-button" type="button" onClick={onBack}>Ir a la canasta</button></div>
      </main>
    );
  }

  const balance = quote?.balance ?? 0;
  const balanceUsed = useBalance ? Math.min(balance, quote?.total ?? 0) : 0;
  const toPay = Math.max((quote?.total ?? 0) - balanceUsed, 0);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setFeedback('');
    try {
      await onSubmit(method, useBalance && balance > 0);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'No pudimos registrar tu pedido.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="page-content pay-view">
      <div className="page-bar">
        <button className="round-button" type="button" onClick={onBack} aria-label="Volver a la canasta"><Icon name="back" size={20} /></button>
        <h1>Confirmar pedido</h1>
        <span className="round-button is-ghost" aria-hidden="true" />
      </div>
      <form className="pay-form" onSubmit={handleSubmit}>
        <div className="pay-main">
          <section className="pay-box" aria-label="Entrega">
            <span className="pay-box-icon" aria-hidden="true"><Icon name="building" size={20} /></span>
            <span><b>{zone ? `${zone.name}${zone.district ? ` · ${zone.district}` : ''}` : 'Tu zona'}</b><small>El {delivery} · {RECEIVES[zone?.reception ?? ''] ?? 'la recibe la portería'}</small></span>
          </section>
          {quote ? (
            <details className="pay-lines">
              <summary>{quote.lines.length} {quote.lines.length === 1 ? 'producto' : 'productos'} en tu canasta<Icon name="chevron" size={18} /></summary>
              <ul>{quote.lines.map((line) => <li key={line.id}><span>{line.name} <small>× {formatQuantity(line.quantity)}</small></span><span>{formatMoney(line.total)}</span></li>)}</ul>
            </details>
          ) : null}

          <fieldset className="pay-methods-group">
            <legend>¿Cómo pagas?</legend>
            {(['YAPE', 'PLIN'] as const).map((value) => (
              <label className={`pay-option ${method === value ? 'is-on' : ''}`} key={value}>
                <input type="radio" name="paymentMethod" value={value} checked={method === value} onChange={() => setMethod(value)} />
                <span className={`pay-logo pay-logo--${value.toLowerCase()}`} aria-hidden="true">{methodName(value)}</span>
                <span className="pay-option-copy"><b>{methodName(value)}</b><small>Te damos un código para el mensaje del pago</small></span>
                <span className="pay-radio" aria-hidden="true" />
              </label>
            ))}
            {balance > 0 ? (
              <label className={`pay-option ${useBalance ? 'is-on' : ''}`}>
                <input type="checkbox" checked={useBalance} onChange={(event) => setUseBalance(event.target.checked)} />
                <span className="pay-logo pay-logo--saldo" aria-hidden="true"><Icon name="wallet" size={18} /></span>
                <span className="pay-option-copy"><b>Usar mi saldo</b><small>Tienes {formatMoney(balance)} a favor</small></span>
                <span className="pay-switch" aria-hidden="true" />
              </label>
            ) : null}
          </fieldset>
        </div>

        <aside className="pay-side">
          <dl className="totals">
            <div><dt>Productos</dt><dd>{formatMoney(quote?.subtotal ?? 0)}</dd></div>
            <div><dt>Envío máximo</dt><dd>{formatMoney(quote?.delivery ?? 0)}</dd></div>
            {balanceUsed ? <div><dt>Con tu saldo</dt><dd>−{formatMoney(balanceUsed)}</dd></div> : null}
            {quote && quote.supermarketSaving > 0 ? <div className="is-saving"><dt>Ahorras frente al súper</dt><dd>{formatMoney(quote.supermarketSaving)}</dd></div> : null}
            <div className="is-total"><dt>{toPay > 0 ? 'Pagas como máximo' : 'Total'}</dt><dd>{formatMoney(toPay > 0 ? toPay : quote?.total ?? 0)}</dd></div>
          </dl>
          {!cycleOpen ? <p className="pay-alert" role="alert"><b>Los pedidos de esta semana ya cerraron.</b> Recibimos pedidos de lunes a miércoles hasta las 8 p. m.; tu canasta queda guardada.</p> : null}
          {feedback ? <p className="pay-alert" role="alert"><b>No pudimos registrar tu pedido.</b> {feedback}</p> : null}
          <p className="pp-note">Si entre todos el precio baja, te devolvemos la diferencia como saldo. Si cancelas antes del miércoles 8 p. m., te devolvemos todo.</p>
          <div className="sticky-cta">
            <button className="primary-button" type="submit" disabled={submitting || !cycleOpen || !quote} aria-busy={submitting}>{submitting ? 'Guardando pedido…' : `Confirmar pedido · ${formatMoney(toPay > 0 ? toPay : quote?.total ?? 0)}`}</button>
          </div>
        </aside>
      </form>
    </main>
  );
}

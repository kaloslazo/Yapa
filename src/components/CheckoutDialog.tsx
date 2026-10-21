import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import type { Order, Quote, Zone } from '../types';
import { Icon } from './Icon';
import { SavingsNote } from './CartPanel';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';

interface CheckoutDialogProps {
  open: boolean;
  quote: Quote | null;
  zone: Zone | undefined;
  cycleOpen: boolean;
  confirmation: Order | null;
  onClose: () => void;
  onSubmit: (method: 'YAPE' | 'PLIN', useBalance: boolean) => Promise<void>;
  onOpenOrders: () => void;
}

const methodName = (method: string) => (method === 'PLIN' ? 'Plin' : 'Yape');

// FE-04: no se escribe nada; Yapa da el código de pago al confirmar (S-150)
export function CheckoutDialog({ open, quote, zone, cycleOpen, confirmation, onClose, onSubmit, onOpenOrders }: CheckoutDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [method, setMethod] = useState<'YAPE' | 'PLIN'>('YAPE');
  const [useBalance, setUseBalance] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
    if (open) {
      setFeedback('');
      setCopied(false);
    }
  }, [open]);

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

  const copyCode = async (code: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <dialog ref={dialogRef} className="checkout-dialog" aria-labelledby="checkout-title" onCancel={(event) => { event.preventDefault(); onClose(); }} onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      {confirmation ? (
        <div className="success-state">
          <div className="success-icon"><Icon name="check" size={30} /></div>
          <span className="dialog-step">Pedido {confirmation.id} registrado</span>
          <h2 id="checkout-title">¡Tu canasta ya está separada!</h2>
          {confirmation.toPay > 0 ? (
            <div className="pay-card">
              <span>Yapea ahora</span>
              <strong className="pay-amount">{formatMoney(confirmation.toPay)}</strong>
              <span>por {methodName(confirmation.method)} y escribe este código en el mensaje:</span>
              <button className="pay-code" type="button" onClick={() => void copyCode(confirmation.paymentCode)} aria-label={`Copiar el código ${confirmation.paymentCode}`}>{confirmation.paymentCode}<Icon name={copied ? 'check' : 'copy'} size={18} /></button>
              <small>{copied ? '¡Copiado!' : 'Toca el código para copiarlo'} · con él verificamos tu pago</small>
            </div>
          ) : <div className="savings-note"><Icon name="wallet" size={20} /><span>Tu saldo cubrió todo: <strong>no tienes que yapear</strong>.</span></div>}
          <ol className="next-steps">
            <li><span>1</span>Verificamos tu pago<small>hoy</small></li>
            <li><span>2</span>Compramos al por mayor<small>jueves</small></li>
            <li><span>3</span>Entregamos en tu portería, con foto<small>sábado</small></li>
            <li><span>4</span>Te devolvemos lo ahorrado como saldo<small>al liquidar</small></li>
          </ol>
          <div className="success-actions"><button className="primary-button" type="button" onClick={onOpenOrders}>Ver mis pedidos <Icon name="arrow" size={17} /></button><button className="secondary-button" type="button" onClick={onClose}>Seguir comprando</button></div>
        </div>
      ) : (
        <>
          <div className="dialog-header"><div><span className="dialog-step">Último paso</span><h2 id="checkout-title">Confirma tu pedido</h2><p>Pagas el precio máximo; lo que ahorremos entre todos te lo devolvemos como saldo.</p></div><button className="icon-button" type="button" onClick={onClose} aria-label="Cerrar"><Icon name="close" size={20} /></button></div>
          <form className="checkout-form" onSubmit={handleSubmit}>
            <fieldset>
              <legend><Icon name="pin" size={18} /> Entrega</legend>
              <div className="zone-note"><Icon name="calendar" size={18} /><span>El sábado en <strong>{zone?.name ?? 'tu zona'}</strong>{zone?.district ? ` · ${zone.district}` : ''}. Recibe la portería.</span></div>
            </fieldset>
            {quote ? <details className="checkout-lines"><summary>{quote.lines.length} productos en tu canasta</summary><table><tbody>{quote.lines.map((line) => <tr key={line.id}><td>{line.name}</td><td>{formatQuantity(line.quantity)}</td><td>{formatMoney(line.total)}</td></tr>)}</tbody></table></details> : null}
            <fieldset>
              <legend><Icon name="wallet" size={18} /> ¿Cómo pagas?</legend>
              <div className="choice-list choice-list--inline">{(['YAPE', 'PLIN'] as const).map((value) => <label className="choice-row" key={value}><input type="radio" name="paymentMethod" value={value} checked={method === value} onChange={() => setMethod(value)} /><span className="choice-mark" /><span className="choice-copy"><strong>{methodName(value)}</strong></span></label>)}</div>
              {balance > 0 ? <label className="choice-row"><input type="checkbox" checked={useBalance} onChange={(event) => setUseBalance(event.target.checked)} /><span className="choice-mark choice-mark--check" /><span className="choice-copy"><strong>Usar mi saldo</strong><small>Tienes {formatMoney(balance)} a favor</small></span></label> : null}
              <p className="field-hint">Al confirmar te damos un <strong>código de pago</strong> para el mensaje de tu {methodName(method)}. No tienes que escribir nada.</p>
            </fieldset>
            {quote ? <SavingsNote savings={quote.supermarketSaving} /> : null}
            <div className="dialog-summary">
              <div><span>Productos a precio máximo</span><strong>{formatMoney(quote?.subtotal ?? 0)}</strong></div>
              <div><span>Envío máximo</span><strong>{formatMoney(quote?.delivery ?? 0)}</strong></div>
              {balanceUsed ? <div><span>Con tu saldo</span><strong>− {formatMoney(balanceUsed)}</strong></div> : null}
            </div>
            <div className="dialog-total"><span>{toPay > 0 ? 'Yapeas hoy' : 'Total'}</span><strong>{formatMoney(toPay > 0 ? toPay : quote?.total ?? 0)}</strong></div>
            {!cycleOpen ? <p className="auth-feedback auth-feedback--error" role="alert">El ciclo está cerrado: los pedidos se reciben de lunes a miércoles hasta las 20:00.</p> : null}
            {feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null}
            <button className="primary-button" type="submit" disabled={submitting || !cycleOpen || !quote} aria-busy={submitting}>{submitting ? 'Guardando pedido…' : 'Confirmar pedido'} {!submitting ? <Icon name="arrow" size={17} /> : null}</button>
            <p className="dialog-disclaimer">Nunca pagas más de lo que ves aquí. Si cancelas antes del miércoles 20:00, te devolvemos todo.</p>
          </form>
        </>
      )}
    </dialog>
  );
}

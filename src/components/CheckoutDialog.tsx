import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { paymentMethods, windowLabel, zoneById, zones } from '../data/catalog';
import type { OrderConfirmation, OrderSelection } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { roundCents } from '../utils/domain';

interface CheckoutDialogProps {
  open: boolean;
  subtotal: number;
  delivery: number;
  total: number;
  balance: number;
  cycleOpen: boolean;
  confirmation: OrderConfirmation | null;
  initialSelection: OrderSelection;
  onClose: () => void;
  onSubmit: (selection: OrderSelection) => void | Promise<void>;
}

export function CheckoutDialog({ open, subtotal, delivery, total, balance, cycleOpen, confirmation, initialSelection, onClose, onSubmit }: CheckoutDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [zoneId, setZoneId] = useState(initialSelection.zoneId);
  const [reference, setReference] = useState(initialSelection.reference);
  const [paymentMethod, setPaymentMethod] = useState(initialSelection.paymentMethod);
  const [operationCode, setOperationCode] = useState('');
  const [useBalance, setUseBalance] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setZoneId(initialSelection.zoneId);
    setReference(initialSelection.reference);
    setPaymentMethod(initialSelection.paymentMethod);
    setOperationCode('');
    setUseBalance(false);
    setFeedback(null);
  }, [initialSelection, open]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const zone = zoneById(zoneId);
  const balanceUsed = useBalance ? Math.min(balance, total) : 0;
  const toPay = roundCents(total - balanceUsed);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFeedback(null);
    setSubmitting(true);
    try {
      await onSubmit({ zoneId, reference, paymentMethod, operationCode, useBalance: balanceUsed });
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'No pudimos registrar el pedido. Inténtalo nuevamente.');
    } finally {
      setSubmitting(false);
    }
  };

  const close = () => onClose();
  const confirmedZone = zoneById(confirmation?.zoneId);

  return (
    <dialog ref={dialogRef} className="checkout-dialog" aria-labelledby="checkout-title" onCancel={(event) => { event.preventDefault(); close(); }} onClick={(event) => { if (event.target === event.currentTarget) close(); }}>
      {confirmation ? (
        <div className="success-state">
          <div className="success-icon"><Icon name="check" size={30} /></div>
          <span className="dialog-step">Pedido registrado</span>
          <h2>Tu canasta ya está separada</h2>
          <p>Pedido <strong>{confirmation.orderCode}</strong> para <strong>{confirmedZone?.name}</strong>, el sábado de <strong>{windowLabel(confirmation.deliveryWindow)}</strong>.</p>
          <div className="success-detail success-detail--stacked">
            <div><span>Pagaste</span><strong>{formatMoney(confirmation.total)}{confirmation.paidBalance ? ` · ${formatMoney(confirmation.paidBalance)} con saldo` : ''}</strong></div>
            <div><span>Pago</span><strong>{confirmation.paymentStatus === 'VERIFICADO' ? 'Confirmado' : `${confirmation.paymentMethod === 'PLIN' ? 'Plin' : 'Yape'} ${confirmation.operationCode} · por verificar`}</strong></div>
          </div>
          <p className="dialog-disclaimer">Después de la entrega te devolvemos como saldo lo que ahorremos entre todos. Si tu zona no llega a 8 pedidos, te devolvemos el 100 % a tu Yape o Plin.</p>
          <button className="primary-button" type="button" onClick={close}>Volver al catálogo <Icon name="arrow" size={17} /></button>
        </div>
      ) : (
        <>
          <div className="dialog-header"><div><span className="dialog-step">Último paso</span><h2 id="checkout-title">Completa tu pedido</h2><p>Pagas el precio máximo; lo que ahorremos entre todos te lo devolvemos como saldo.</p></div><button className="icon-button" type="button" onClick={close} aria-label="Cerrar"><Icon name="close" size={20} /></button></div>
          <form className="checkout-form" onSubmit={handleSubmit}>
            <fieldset>
              <legend><Icon name="pin" size={18} /> Tu zona de recepción</legend>
              <label htmlFor="zone">Punto de recepción</label>
              <select id="zone" name="zone" value={zoneId} onChange={(event) => setZoneId(event.target.value)}>
                {zones.map((item) => <option key={item.id} value={item.id} disabled={!item.active}>{item.name} · {item.district}{item.active ? '' : ' (pronto)'}</option>)}
              </select>
              <label className="checkout-field"><span>Departamento o referencia <small>opcional</small></span><input name="reference" value={reference} onChange={(event) => setReference(event.target.value)} placeholder="Ej. Dpto. 302, torre B" /></label>
              <div className="zone-note"><Icon name="calendar" size={18} /><span>Entrega el sábado de <strong>{windowLabel(zone?.deliveryWindow)}</strong> en la portería. Yapa asigna la ventana a cada zona.</span></div>
            </fieldset>
            <fieldset>
              <legend><Icon name="wallet" size={18} /> Pago por adelantado</legend>
              {balance > 0 ? <label className="choice-row"><input type="checkbox" checked={useBalance} onChange={(event) => setUseBalance(event.target.checked)} /><span className="choice-mark choice-mark--check" /><span className="choice-copy"><strong>Usar mi saldo</strong><small>Tienes {formatMoney(balance)} a favor</small></span></label> : null}
              {toPay > 0 ? <>
                <div className="choice-list choice-list--inline">{paymentMethods.map((method) => <label className="choice-row" key={method.value}><input type="radio" name="paymentMethod" value={method.value} checked={paymentMethod === method.value} onChange={() => setPaymentMethod(method.value)} /><span className="choice-mark" /><span className="choice-copy"><strong>{method.label}</strong></span></label>)}</div>
                <p className="field-hint">Yapea <strong>{formatMoney(toPay)}</strong> y escribe el código de operación de tu comprobante. El equipo lo verifica antes del cierre.</p>
                <label className="checkout-field"><span>Código de operación</span><input name="operationCode" value={operationCode} onChange={(event) => setOperationCode(event.target.value)} placeholder="Ej. 04512873" inputMode="numeric" autoComplete="off" /></label>
              </> : <p className="field-hint">Tu saldo cubre todo el pedido; no hace falta yapear.</p>}
            </fieldset>
            <div className="dialog-summary">
              <div><span>Productos a precio máximo</span><strong>{formatMoney(subtotal)}</strong></div>
              <div><span>Envío máximo</span><strong>{formatMoney(delivery)}</strong></div>
              {balanceUsed ? <div><span>Con tu saldo</span><strong>− {formatMoney(balanceUsed)}</strong></div> : null}
            </div>
            <div className="dialog-total"><span>{toPay > 0 ? 'Yapeas hoy' : 'Total'}</span><strong>{formatMoney(toPay > 0 ? toPay : total)}</strong></div>
            {!cycleOpen ? <p className="auth-feedback auth-feedback--error" role="alert">El ciclo está cerrado: los pedidos se reciben de lunes a miércoles hasta las 20:00.</p> : null}
            {feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null}
            <button className="primary-button" type="submit" disabled={submitting || !cycleOpen} aria-busy={submitting}>{submitting ? 'Guardando pedido…' : 'Registrar pedido'} {!submitting ? <Icon name="arrow" size={17} /> : null}</button>
            <p className="dialog-disclaimer">Nunca pagas más de lo que ves aquí. Si cancelas antes del miércoles 20:00, te devolvemos todo.</p>
          </form>
        </>
      )}
    </dialog>
  );
}

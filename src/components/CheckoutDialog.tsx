import { useEffect, useRef, useState } from 'react';
import type { FormEvent, MouseEvent } from 'react';
import { deliveryWindows, paymentMethods } from '../data/catalog';
import type { OrderConfirmation, OrderSelection } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';
import { validateOrderSelection } from '../utils/domain';

interface CheckoutDialogProps {
  open: boolean;
  subtotal: number;
  deliveryFee: number;
  confirmation: OrderConfirmation | null;
  initialSelection: OrderSelection;
  onClose: () => void;
  onSubmit: (selection: OrderSelection) => void | Promise<void>;
}

export function CheckoutDialog({ open, subtotal, deliveryFee, confirmation, initialSelection, onClose, onSubmit }: CheckoutDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [district, setDistrict] = useState(initialSelection.district);
  const [deliveryWindow, setDeliveryWindow] = useState(initialSelection.deliveryWindow);
  const [paymentMethod, setPaymentMethod] = useState(initialSelection.paymentMethod);
  const [addressLine, setAddressLine] = useState(initialSelection.addressLine);
  const [reference, setReference] = useState(initialSelection.reference);
  const [coordinates, setCoordinates] = useState(initialSelection.coordinates);
  const [mapPoint, setMapPoint] = useState(() => districtPoint(initialSelection.district));
  const [feedback, setFeedback] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    setDistrict(initialSelection.district);
    setDeliveryWindow(initialSelection.deliveryWindow);
    setPaymentMethod(initialSelection.paymentMethod);
    setAddressLine(initialSelection.addressLine);
    setReference(initialSelection.reference);
    setCoordinates(initialSelection.coordinates);
    setMapPoint(districtPoint(initialSelection.district));
    setFeedback(null);
  }, [initialSelection]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const selection = { district, deliveryWindow, paymentMethod, addressLine, reference, coordinates };
    const validationMessage = validateOrderSelection(selection, subtotal);
    if (validationMessage) {
      setFeedback(validationMessage);
      return;
    }
    setFeedback(null);
    setSubmitting(true);
    try {
      await onSubmit(selection);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : 'No pudimos registrar el pedido. Inténtalo nuevamente.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDistrictChange = (nextDistrict: string) => {
    const nextPoint = districtPoint(nextDistrict);
    setDistrict(nextDistrict);
    setMapPoint(nextPoint);
    setCoordinates({ lat: nextPoint.lat, lng: nextPoint.lng });
  };

  const handleMapClick = (event: MouseEvent<HTMLButtonElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = Math.max(8, Math.min(92, ((event.clientX - bounds.left) / bounds.width) * 100));
    const y = Math.max(12, Math.min(86, ((event.clientY - bounds.top) / bounds.height) * 100));
    setMapPoint({ x, y, lat: -12.07 + (y - 50) * 0.00042, lng: -77.04 + (x - 50) * 0.00055 });
  };

  const close = () => onClose();
  const selectedPayment = paymentMethods.find((method) => method.value === (confirmation?.paymentMethod ?? paymentMethod));
  const selectedWindow = deliveryWindows.find((window) => window.code === (confirmation?.deliveryWindow ?? deliveryWindow));

  return (
    <dialog ref={dialogRef} className="checkout-dialog" aria-labelledby="checkout-title" onCancel={(event) => { event.preventDefault(); close(); }} onClick={(event) => { if (event.target === event.currentTarget) close(); }}>
      {confirmation ? (
        <div className="success-state"><div className="success-icon"><Icon name="check" size={30} /></div><span className="dialog-step">Pedido registrado</span><h2>Tu canasta ya está separada</h2><p>Hemos creado el pedido <strong>{confirmation.orderCode}</strong> para <strong>{confirmation.district}</strong>, el sábado de <strong>{selectedWindow?.label}</strong>.</p><div className="success-detail success-detail--stacked"><div><span>Entrega</span><strong>{confirmation.addressLine}</strong></div><div><span>Medio de pago</span><strong>{selectedPayment?.label}</strong></div></div><button className="primary-button" type="button" onClick={close}>Volver al catálogo <Icon name="arrow" size={17} /></button><p className="dialog-disclaimer">En una versión conectada, aquí recibirías la confirmación y el estado del pago.</p></div>
      ) : (
        <>
          <div className="dialog-header"><div><span className="dialog-step">Último paso</span><h2 id="checkout-title">Completa tu pedido</h2><p>Reserva tu canasta para la entrega del sábado.</p></div><button className="icon-button" type="button" onClick={close} aria-label="Cerrar"><Icon name="close" size={20} /></button></div>
          <form className="checkout-form" onSubmit={handleSubmit}>
            <fieldset><legend><Icon name="pin" size={18} /> Dirección de entrega</legend><label htmlFor="district">Distrito piloto</label><select id="district" name="district" value={district} onChange={(event) => handleDistrictChange(event.target.value)}><option>Lince</option><option>Jesús María</option><option>La Victoria</option></select><div className="address-fields"><label className="checkout-field"><span>Dirección</span><input name="addressLine" value={addressLine} onChange={(event) => setAddressLine(event.target.value)} placeholder="Ej. Av. Arequipa 1234, dpto. 302" autoComplete="street-address" /></label><label className="checkout-field"><span>Referencia <small>opcional</small></span><input name="reference" value={reference} onChange={(event) => setReference(event.target.value)} placeholder="Portería, parque o color de fachada" /></label></div><div className="map-picker"><div className="map-picker-heading"><span>Ubicación aproximada</span><small>Mapa simulado · preparado para API</small></div><button className="map-surface" type="button" onClick={handleMapClick} aria-label="Seleccionar ubicación en el mapa simulado"><span className="map-road map-road--one" /><span className="map-road map-road--two" /><span className="map-road map-road--three" /><span className="map-neighborhood map-neighborhood--one" /><span className="map-neighborhood map-neighborhood--two" /><span className="map-pin" style={{ left: `${mapPoint.x}%`, top: `${mapPoint.y}%` }}><Icon name="pin" size={20} weight="fill" /></span><span className="map-label">{district}</span></button><div className="map-picker-footer"><span>Pin: {coordinates.lat.toFixed(4)}, {coordinates.lng.toFixed(4)}</span><button className="text-button" type="button" onClick={() => { const nextPoint = districtPoint(district); setMapPoint(nextPoint); setCoordinates({ lat: nextPoint.lat, lng: nextPoint.lng }); }}>Centrar en distrito</button></div></div><p className="field-hint">Puedes mover el pin; la dirección exacta se confirmará antes de despachar.</p></fieldset>
            <fieldset><legend><Icon name="calendar" size={18} /> Ventana del sábado</legend><div className="choice-list">{deliveryWindows.map((window) => <label className="choice-row" key={window.code}><input type="radio" name="deliveryWindow" value={window.code} checked={deliveryWindow === window.code} onChange={() => setDeliveryWindow(window.code)} /><span className="choice-mark" /><span className="choice-copy"><strong>{window.label}</strong><small>{window.capacity}</small></span></label>)}</div></fieldset>
            <fieldset><legend><Icon name="wallet" size={18} /> Medio de pago</legend><div className="choice-list">{paymentMethods.map((method) => <label className="choice-row" key={method.value}><input type="radio" name="paymentMethod" value={method.value} checked={paymentMethod === method.value} onChange={() => setPaymentMethod(method.value)} /><span className="choice-mark" /><span className="choice-copy"><strong>{method.label}</strong><small>{method.note}</small></span></label>)}</div></fieldset>
            <div className="dialog-total"><span>Total estimado</span><strong>{formatMoney(subtotal + deliveryFee)}</strong></div>
            {feedback ? <p className="auth-feedback auth-feedback--error" role="alert">{feedback}</p> : null}
            <button className="primary-button" type="submit" disabled={submitting} aria-busy={submitting}>{submitting ? 'Guardando pedido…' : 'Registrar pedido'} {!submitting ? <Icon name="arrow" size={17} /> : null}</button>
            <p className="dialog-disclaimer">Esto es un prototipo local: no se realiza ningún cobro ni se envía una dirección real.</p>
          </form>
        </>
      )}
    </dialog>
  );
}

function districtPoint(district: string) {
  const points: Record<string, { x: number; y: number; lat: number; lng: number }> = {
    Lince: { x: 55, y: 45, lat: -12.0841, lng: -77.0317 },
    'Jesús María': { x: 40, y: 58, lat: -12.0784, lng: -77.0502 },
    'La Victoria': { x: 72, y: 68, lat: -12.0736, lng: -77.0173 },
  };
  return points[district] || points.Lince;
}

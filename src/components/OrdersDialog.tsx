import { useEffect, useRef } from 'react';
import type { OrderRecord } from '../types';
import { Icon } from './Icon';
import { formatMoney } from '../utils/format';

interface OrdersDialogProps {
  open: boolean;
  orders: OrderRecord[];
  onClose: () => void;
}

export function OrdersDialog({ open, orders, onClose }: OrdersDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog ref={dialogRef} className="checkout-dialog orders-dialog" aria-labelledby="orders-title" onCancel={(event) => { event.preventDefault(); onClose(); }} onClick={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <div className="dialog-header"><div><span className="dialog-step">Tu cuenta</span><h2 id="orders-title">Mis pedidos</h2><p>Revisa tus canastas registradas y su estado.</p></div><button className="icon-button" type="button" onClick={onClose} aria-label="Cerrar mis pedidos"><Icon name="close" size={20} /></button></div>
      {orders.length ? <div className="orders-list">{orders.map((order) => <article className="order-row" key={order.orderCode}><div className="order-row-top"><div><strong>{order.orderCode}</strong><span>{formatDate(order.createdAt)}</span></div><span className="order-status">{order.status}</span></div><p>{order.itemCount} productos · {order.district} · sábado {formatWindow(order.deliveryWindow)}</p><div className="order-row-bottom"><span>{order.addressLine}</span><strong>{formatMoney(order.total)}</strong></div></article>)}</div> : <div className="orders-empty"><span className="cart-empty-art"><Icon name="box" size={26} /></span><h3>Aún no tienes pedidos</h3><p>Cuando registres una canasta, la verás aquí.</p></div>}
    </dialog>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('es-PE', { day: 'numeric', month: 'short' }).format(new Date(value));
}

function formatWindow(code: string) {
  const labels: Record<string, string> = { SAT_09_12: '09:00–12:00', SAT_12_15: '12:00–15:00', SAT_15_18: '15:00–18:00' };
  return labels[code] || code;
}

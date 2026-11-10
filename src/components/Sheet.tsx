import { useEffect, useRef, type ReactNode } from 'react';
import type { Product } from '../types';
import { Icon } from './Icon';
import { ProductVisual, savingPercent, unitLabel } from './Catalog';
import { formatMoney } from '../utils/format';
import { formatQuantity } from '../utils/cart';

// hoja que sube desde abajo en el celular y queda al centro en la compu; Escape o tocar afuera la cierra
export function Sheet({ label, onClose, children }: { label: string; onClose: () => void; children: ReactNode }) {
  const panel = useRef<HTMLDivElement>(null);
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const before = document.activeElement as HTMLElement | null;
    panel.current?.focus();
    const key = (event: KeyboardEvent) => { if (event.key === 'Escape') close.current(); };
    document.addEventListener('keydown', key);
    return () => { document.removeEventListener('keydown', key); before?.focus?.(); };
  }, []);
  return (
    <div className="sheet-layer">
      <div className="sheet-scrim" onClick={() => close.current()} aria-hidden="true" />
      <div className="sheet" role="dialog" aria-modal="true" aria-label={label} tabIndex={-1} ref={panel}>
        <button className="sheet-close" type="button" onClick={() => close.current()} aria-label="Cerrar"><Icon name="close" size={20} /></button>
        {children}
      </div>
    </div>
  );
}

interface ProductSheetProps {
  product: Product;
  quantity: number;
  onAdd: (product: Product) => void;
  onDecrease: (product: Product) => void;
  onClose: () => void;
}

// la ficha: aquí sí va el detalle (ahorro por unidad y el tramo que viene), no en la grilla
export function ProductSheet({ product, quantity, onAdd, onDecrease, onClose }: ProductSheetProps) {
  const unit = unitLabel(product.unit);
  const per = product.unit === 'unidad' ? 'unidad' : product.unit === 'kg' ? 'kilo' : product.unit;
  const off = savingPercent(product);
  const next = product.nextTier;
  const reached = product.tiers.filter((t) => t.from <= product.ordered).map((t) => t.from);
  const from = reached.length ? Math.max(...reached) : 0;
  const progress = next ? Math.min(Math.max((product.ordered - from) / (next.from - from || 1), 0), 1) * 100 : 100;
  return (
    <Sheet label={product.name} onClose={onClose}>
      <div className="sheet-photo">
        <ProductVisual product={product} />
        {off ? <span className="shop-off">−{off}%</span> : null}
      </div>
      <h2 className="sheet-title">{product.name}</h2>
      <p className="sheet-detail">{product.detail}</p>
      <p className="sheet-price"><strong>{formatMoney(product.price)}</strong> por {per}</p>
      {off && product.supermarket ? <p className="sheet-saving">Ahorras {formatMoney(product.supermarket.price - product.price)} por {unit} frente a {product.supermarket.source}</p> : null}
      {next ? (
        <div className="sheet-drop">
          <p>Si entre todos llegamos a <strong>{formatQuantity(next.from)} {unit}</strong>, baja a <strong>{formatMoney(next.price)}</strong> y te devolvemos la diferencia. Van {formatQuantity(product.ordered)} {unit}.</p>
          <span className="sheet-drop-bar" aria-hidden="true"><span style={{ width: `${progress}%` }} /></span>
        </div>
      ) : product.tiers.length > 1 ? <div className="sheet-drop"><p>Ya llegamos al mejor precio de la semana.</p></div> : null}
      <div className="sheet-actions">
        {quantity ? (
          <>
            <div className="sheet-stepper" aria-label={`Cantidad de ${product.name}`}>
              <button type="button" onClick={() => onDecrease(product)} aria-label={`Quitar de ${product.name}`}><Icon name="minus" size={18} weight="bold" /></button>
              <span>{formatQuantity(quantity)} {unit}</span>
              <button type="button" onClick={() => onAdd(product)} disabled={quantity >= product.maxPerOrder} aria-label={`Agregar más ${product.name}`}><Icon name="plus" size={18} weight="bold" /></button>
            </div>
            <button className="primary-button" type="button" onClick={onClose}>Listo</button>
          </>
        ) : <button className="primary-button" type="button" onClick={() => onAdd(product)}>Agregar · {formatMoney(product.price)}</button>}
      </div>
      <p className="sheet-note">Hasta {formatQuantity(product.maxPerOrder)} {unit} por vecino, para que alcance para todos.</p>
    </Sheet>
  );
}

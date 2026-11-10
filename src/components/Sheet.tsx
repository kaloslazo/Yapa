import { useEffect, useRef, type ReactNode } from 'react';
import { Icon } from './Icon';

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

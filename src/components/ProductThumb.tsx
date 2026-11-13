import type { CSSProperties } from 'react';
import { lookFor } from '../data/presentation';

// foto chica de un producto para listas del panel y de los pedidos (S-328); el nombre va al lado, así que es decorativa
export function ProductThumb({ id, size = 44 }: { id: string; size?: number }) {
  const look = lookFor(id, '');
  return (
    <span className="product-thumb" style={{ '--tint': look.tint, width: size, height: size } as CSSProperties} aria-hidden="true">
      {look.image ? <img src={look.image} alt="" width={size} height={size} loading="lazy" /> : <span>{look.emoji}</span>}
    </span>
  );
}

import { useState } from 'react';
import { Icon } from './Icon';

// la fuente la escribe el equipo a mano; se normaliza para reconocer la cadena
const STORES: Record<string, { name: string; logo: string }> = {
  'plaza vea': { name: 'Plaza Vea', logo: '/images/tiendas/plaza-vea.svg' },
  plazavea: { name: 'Plaza Vea', logo: '/images/tiendas/plaza-vea.svg' },
  tottus: { name: 'Tottus', logo: '/images/tiendas/tottus.svg' },
  metro: { name: 'Metro', logo: '/images/tiendas/metro.svg' },
  wong: { name: 'Wong', logo: '/images/tiendas/wong.svg' },
  makro: { name: 'Makro', logo: '/images/tiendas/makro.svg' },
  vivanda: { name: 'Vivanda', logo: '/images/tiendas/vivanda.svg' },
  mass: { name: 'Mass', logo: '/images/tiendas/mass.svg' },
};

export function StoreMark({ source }: { source: string }) {
  const store = STORES[source.trim().toLowerCase()];
  const [broken, setBroken] = useState(false);
  if (store && !broken) return <img className="store-logo" src={store.logo} alt={store.name} title={store.name} height="18" onError={() => setBroken(true)} />;
  // sin logo: nombre corto con ícono de tienda, para mercados y cadenas sin archivo
  return <span className="store-name" title={source}><Icon name="store" size={14} />{store?.name ?? source}</span>;
}

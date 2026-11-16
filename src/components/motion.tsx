// movimiento de la tienda en css plano (ideas de React Bits y Magic UI, sin librerías)
// con prefers-reduced-motion se ve el valor final al tiro
import { useEffect, useRef, useState } from 'react';

export const reducedMotion = () => typeof window !== 'undefined' && Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches);

// true una sola vez, cuando el elemento entra en pantalla
export function useInView<T extends Element>(threshold = 0.15) {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || inView) return;
    if (typeof IntersectionObserver === 'undefined' || reducedMotion()) { setInView(true); return; }
    const io = new IntersectionObserver(([entry]) => { if (entry.isIntersecting) { setInView(true); io.disconnect(); } }, { threshold, rootMargin: '0px 0px -5% 0px' });
    io.observe(el);
    return () => io.disconnect();
  }, [inView, threshold]);
  return [ref, inView] as const;
}

// counter (react bits): cada dígito es una tira 0-9 que rueda hasta su valor
export function RollingNumber({ value, className = '' }: { value: string; className?: string }) {
  const [ready, setReady] = useState(reducedMotion);
  useEffect(() => { const id = requestAnimationFrame(() => setReady(true)); return () => cancelAnimationFrame(id); }, []);
  const chars = [...value];
  return (
    <span className={`rolling ${className}`}>
      <span className="sr-only">{value}</span>
      <span className="rolling-track" aria-hidden="true">
        {chars.map((ch, i) => {
          const key = chars.length - i; // desde la derecha, así las unidades siguen siendo las unidades
          return /\d/.test(ch)
            ? <span className="rolling-digit" key={`d${key}`}><span className="rolling-strip" style={{ transform: `translateY(-${(ready ? Number(ch) : 0) * 10}%)` }}>{DIGITS.map((d) => <span key={d}>{d}</span>)}</span></span>
            : <span className="rolling-char" key={`c${key}`}>{ch}</span>;
        })}
      </span>
    </span>
  );
}
const DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];

const SPOTLIGHT = '.partner-card, .route-stop, .route-planner, .photo-product-review, .partner-empty';
// spotlight card (react bits): el brillo sigue al puntero dentro de la tarjeta que se toca; un solo oyente por pantalla
export function spotlight(event: React.PointerEvent<HTMLElement>) {
  if (event.pointerType !== 'mouse') return;
  const card = (event.target as HTMLElement).closest<HTMLElement>(SPOTLIGHT);
  if (!card) return;
  const box = card.getBoundingClientRect();
  card.style.setProperty('--mx', `${event.clientX - box.left}px`);
  card.style.setProperty('--my', `${event.clientY - box.top}px`);
}

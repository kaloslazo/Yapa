export type ToastTone = 'neutral' | 'success' | 'warning';

export interface Toast {
  title: string;
  detail?: string;
  tone: ToastTone;
  action?: { label: string; run: () => void };
}

export function toastDuration(tone: ToastTone, detail?: string): number {
  // con detalle se da más tiempo para leerlo
  return (tone === 'warning' ? 9000 : 6000) + (detail ? 2000 : 0);
}

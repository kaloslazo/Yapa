export type ToastTone = 'neutral' | 'success' | 'warning';

export function toastDuration(tone: ToastTone): number {
  return tone === 'warning' ? 9000 : 6000;
}

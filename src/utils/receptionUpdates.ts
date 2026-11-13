export interface ReceptionEvent { estado: string; hora: string }
export interface ReceptionSnapshot { ciclo: string; zona: { id: string }; seguimiento?: string; hitos?: ReceptionEvent[] }

export const RECEPTION_LABELS: Record<string, string> = {
  sin_pedidos: 'Sin pedidos', preparando: 'En preparación', listo: 'Listo para despacho',
  en_camino: 'En camino', entregada: 'Llegó al edificio', recibida: 'Recepción confirmada', fallida: 'No se pudo entregar',
};

export function unseenReceptionEvents(previous: ReceptionSnapshot | null, current: ReceptionSnapshot): ReceptionEvent[] {
  if (!previous || previous.ciclo !== current.ciclo || previous.zona.id !== current.zona.id) return [];
  const seen = new Set((previous.hitos ?? []).map(e => `${e.estado}:${e.hora}`));
  const updates = (current.hitos ?? []).filter(e => !seen.has(`${e.estado}:${e.hora}`));
  // Preparación y ausencia de pedidos no tienen hora propia en el motor.
  if (current.seguimiento && previous.seguimiento !== current.seguimiento && !updates.some(e => e.estado === current.seguimiento)) {
    updates.push({ estado: current.seguimiento, hora: '' });
  }
  return updates;
}

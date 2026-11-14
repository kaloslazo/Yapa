// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { expect, it, vi } from 'vitest';
import { RoutePlanner } from './RoutePlanner';
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
it('muestra puntos, advierte coordenadas faltantes y aplica el orden calculado', async () => {
  const host = document.createElement('div'); document.body.append(host); const root = createRoot(host); const apply = vi.fn();
  const stops = [-77, -77.02, -77.01, null].map((lon, i) => ({ zona: { id: String(i), nombre: `Edificio ${i}`, lat: -12, lon }, estado: 'pendiente', pedidos: [{ id: i, bolsas: 1 }] }));
  try {
    await act(async () => root.render(createElement(RoutePlanner, { stops, active: false, onOrder: apply })));
    expect(host.querySelectorAll('svg circle')).toHaveLength(3); expect(host.textContent).toContain('Sin coordenadas: Edificio 3');
    await act(async () => host.querySelector<HTMLButtonElement>('.primary-button')!.click());
    expect(apply).toHaveBeenCalledWith(['0', '2', '1', '3']); expect(host.textContent).toContain('no representa calles');
  } finally { await act(async () => root.unmount()); host.remove(); }
});

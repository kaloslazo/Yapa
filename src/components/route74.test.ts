// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, expect, it, vi } from 'vitest';
import { RoutePlanner } from './RoutePlanner';
import { api } from '../services/api';
vi.mock('../services/api',()=>({api:{post:vi.fn()}}));
vi.mock('./LazyRouteMap',()=>({LazyRouteMap:({geometry}:{geometry?:number[][]})=>createElement('div',{'data-road':geometry?.length??0})}));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
let host:HTMLDivElement,root:Root;
afterEach(async()=>{await act(async()=>root.unmount());host.remove();vi.clearAllMocks();});
const stops=[{zona:{id:'A',nombre:'A',lat:-12,lon:-77},estado:'pendiente',pedidos:[{id:1,bolsas:1}]},{zona:{id:'B',nombre:'B',lat:-12.01,lon:-77.01},estado:'pendiente',pedidos:[{id:2,bolsas:1}]}];
async function mount(){host=document.createElement('div');document.body.append(host);root=createRoot(host);await act(async()=>root.render(createElement(RoutePlanner,{stops,cycle:'2026-W40',active:false,onOrder:vi.fn()})));}
it('traza solo bajo petición y conserva distancia vial separada de la heurística',async()=>{
 vi.mocked(api.post).mockResolvedValue({distancia_m:2500,duracion_s:600,coordenadas:[[-77,-12],[-77.01,-12.01]]});
 await mount();expect(api.post).not.toHaveBeenCalled();
 await act(async()=>[...host.querySelectorAll<HTMLButtonElement>('button')].find(b=>b.textContent==='Trazar por calles')!.click());
 expect(api.post).toHaveBeenCalledWith('/api/reparto/ruta',{ciclo:'2026-W40',zonas:'["A","B"]'});
 expect(host.textContent).toContain('Recorrido vial: 2.50 km');expect(host.querySelector('[data-road]')!.getAttribute('data-road')).toBe('2');
});
it('muestra el fallo y no inventa geometría',async()=>{
 vi.mocked(api.post).mockRejectedValue(new Error('Servicio no disponible'));await mount();
 await act(async()=>[...host.querySelectorAll<HTMLButtonElement>('button')].find(b=>b.textContent==='Trazar por calles')!.click());
 expect(host.querySelector('[role=alert]')!.textContent).toContain('Servicio no disponible');expect(host.querySelector('[data-road]')!.getAttribute('data-road')).toBe('0');
});

// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { SupplierStock } from './SupplierStock';
import { SupplierListEditor } from './SupplierListEditor';
import { api } from '../services/api';
vi.mock('../services/api',()=>({api:{get:vi.fn(),post:vi.fn()}}));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
let host:HTMLDivElement,root:Root;
beforeEach(()=>{host=document.createElement('div');document.body.append(host);root=createRoot(host);vi.stubGlobal('URL',{createObjectURL:vi.fn(()=>'blob:photo'),revokeObjectURL:vi.fn()});});
afterEach(async()=>{await act(async()=>root.unmount());host.remove();vi.clearAllMocks();vi.unstubAllGlobals();});
it('requiere peso, confirma carga y aplica el total devuelto al borrador',async()=>{
 const apply=vi.fn();vi.mocked(api.get).mockResolvedValue({productos:[]});
 vi.mocked(api.post).mockResolvedValueOnce({productos:[{producto:'papa',cantidad:3}]}).mockResolvedValueOnce({productos:[{id:'PAPA-AMARILLA',nombre:'Papa amarilla',cantidad:'2.5',disponible:'2',unidades:3,unidad:'kg'}]});
 await act(async()=>root.render(createElement(SupplierStock,{cycle:'2026-W40',candidates:[{id:'PAPA-AMARILLA',name:'Papa amarilla',unit:'kg'}],onApply:apply})));
 const file=host.querySelector('input[type=file]')!;Object.defineProperty(file,'files',{value:[new File(['x'],'foto.jpg',{type:'image/jpeg'})]});
 await act(async()=>file.dispatchEvent(new Event('change',{bubbles:true})));
 expect(host.querySelector<HTMLButtonElement>('[aria-label="Confirmar producto 1"]')!.disabled).toBe(true);
 const weight=host.querySelectorAll('input[type=number]')[1];
 await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(weight,'2.5');weight.dispatchEvent(new Event('input',{bubbles:true}));});
 await act(async()=>host.querySelector<HTMLButtonElement>('[aria-label="Confirmar producto 1"]')!.click());
 await act(async()=>host.querySelector<HTMLButtonElement>('.primary-button')!.click());
 expect(api.post).toHaveBeenLastCalledWith('/api/proveedor/stock/confirmar',expect.any(FormData));
 expect(apply.mock.calls[0][0][0].disponible).toBe('2');expect(host.textContent).toContain('3 unidades visibles');
});
it('precios por volumen comienza cerrado en cada producto',async()=>{
 await act(async()=>root.render(createElement(SupplierListEditor,{initialText:'PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,40,SUP-FRESCOS,0,3.60\nAJO,Ajo,FRESCOS,kg,0.25,40,SUP-FRESCOS,0,4.80',busy:false,resubmit:false,onSubmit:vi.fn()})));
 expect(host.querySelectorAll('.supplier-volume')).toHaveLength(2);expect(host.querySelectorAll('.supplier-volume[open]')).toHaveLength(0);
});

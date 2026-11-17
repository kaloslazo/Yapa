// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { PhotoProductReview } from './PhotoProductReview';
import { api } from '../services/api';
vi.mock('../services/api', () => ({ api: { post: vi.fn() } }));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
let host: HTMLDivElement, root: Root;
const confirm = vi.fn();
beforeEach(async () => {
  vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:photo'), revokeObjectURL: vi.fn() });
  confirm.mockReset(); confirm.mockResolvedValue(true); vi.mocked(api.post).mockReset();
  host=document.createElement('div');document.body.append(host);root=createRoot(host);
  await act(async () => root.render(createElement(PhotoProductReview, { onConfirm: confirm })));
});
afterEach(async () => { await act(async () => root.unmount());host.remove();vi.unstubAllGlobals(); });
async function upload() {
  const input=host.querySelector<HTMLInputElement>('input[type=file]')!;const file=new File(['foto'],'bolsa.jpg',{type:'image/jpeg'});
  Object.defineProperty(input,'files',{configurable:true,value:[file]});
  await act(async () => input.dispatchEvent(new Event('change',{bubbles:true})));return file;
}
async function quantity(value:string) {
  const input=host.querySelector<HTMLInputElement>('input[type=number]')!;
  await act(async () => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,value);input.dispatchEvent(new Event('input',{bubbles:true})); });
}
it('corrige el conteo y confirma con la misma foto, sin guardar automáticamente', async () => {
  vi.mocked(api.post).mockResolvedValue({productos:[{producto:'zanahoria',cantidad:3,confianza:.6}]});
  const file=await upload(); expect(confirm).not.toHaveBeenCalled(); await quantity('2');
  await act(async () => host.querySelector<HTMLButtonElement>('.primary-button')!.click());
  expect(confirm).toHaveBeenCalledWith(file,[{producto:'zanahoria',cantidad:2,confianza:undefined}]); expect(host.textContent).toContain('Confirmado por ti');
  expect(host.querySelector<HTMLInputElement>('input[type=number]')!.disabled).toBe(true);
  await act(async () => host.querySelector<HTMLButtonElement>('.primary-button')!.click());
  expect(confirm).toHaveBeenCalledTimes(1);
});
it('permite revisión manual si el análisis falla y rechaza cantidades inválidas', async () => {
  vi.mocked(api.post).mockRejectedValue(new Error('Análisis no instalado')); await upload();
  await act(async () => [...host.querySelectorAll('button')].find(b=>b.textContent==='Añadir producto manualmente')!.click());
  await quantity('0');expect(host.querySelector<HTMLButtonElement>('.primary-button')!.disabled).toBe(true);
  await quantity('1');expect(host.querySelector<HTMLButtonElement>('.primary-button')!.disabled).toBe(false);
});
it('conserva las correcciones si guardar falla', async () => {
  vi.mocked(api.post).mockResolvedValue({productos:[{producto:'ajo',cantidad:2}]});confirm.mockResolvedValue(false);await upload();
  await act(async () => host.querySelector<HTMLButtonElement>('.primary-button')!.click());
  expect(host.querySelector<HTMLInputElement>('input[type=number]')!.value).toBe('2');expect(host.textContent).not.toContain('Confirmado por ti');
});
it('ignora la respuesta de una foto anterior al elegir otra', async () => {
  let resolve!: (value: unknown)=>void;
  vi.mocked(api.post).mockImplementationOnce(()=>new Promise(r=>{resolve=r;}) as never).mockResolvedValueOnce({productos:[{producto:'cebolla',cantidad:1}]});
  await upload();await upload();await act(async()=>resolve({productos:[{producto:'papa',cantidad:8}]}));
  expect(host.querySelector<HTMLSelectElement>('select')!.value).toBe('cebolla');
});

it('exige elegir la variedad de papa y confirmar la fila antes de guardar', async () => {
  const candidates=[{id:'PAPA-AMARILLA',name:'Papa amarilla',unit:'kg'},{id:'PAPA-BLANCA',name:'Papa blanca',unit:'kg'}];
  vi.mocked(api.post).mockResolvedValue({productos:[{producto:'papa',cantidad:3}]});
  await act(async()=>root.render(createElement(PhotoProductReview,{onConfirm:confirm,candidates})));
  await upload();expect(host.querySelector<HTMLSelectElement>('select')!.value).toBe('');
  expect(host.querySelector<HTMLButtonElement>('.primary-button')!.disabled).toBe(true);
  await act(async()=>{const select=host.querySelector('select')!;select.value='PAPA-BLANCA';select.dispatchEvent(new Event('change',{bubbles:true}));});
  await act(async()=>host.querySelector<HTMLButtonElement>('[aria-label="Confirmar producto 1"]')!.click());
  await act(async()=>host.querySelector<HTMLButtonElement>('.primary-button')!.click());
  expect(confirm.mock.calls[0][1][0]).toMatchObject({codigo:'PAPA-BLANCA',cantidad:3,confirmado:true});
});

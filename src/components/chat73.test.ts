// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, expect, it, vi } from 'vitest';
import { FaqChatbot } from './FaqChatbot';
import { api } from '../services/api';
vi.mock('../services/api',async original=>({...await original<typeof import('../services/api')>(),api:{post:vi.fn()}}));
(globalThis as any).IS_REACT_ACT_ENVIRONMENT=true;
let root:Root,host:HTMLDivElement;
afterEach(async()=>{await act(async()=>root.unmount());host.remove();vi.clearAllMocks();});
async function start(){host=document.createElement('div');document.body.append(host);root=createRoot(host);await act(async()=>root.render(createElement(FaqChatbot)));await act(async()=>host.querySelector<HTMLButtonElement>('.faq-chat-launcher')!.click());}
async function ask(text:string){const input=host.querySelector('input')!;await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')!.set!.call(input,text);input.dispatchEvent(new Event('input',{bubbles:true}));});await act(async()=>host.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})));}
it('propone opciones para pagos sin llamar a IA y añade la respuesta al final',async()=>{
 await start();await ask('pagué');expect(api.post).not.toHaveBeenCalled();
 expect(host.querySelector('[role=log]')!.textContent).toContain('pagué');
 const option=[...host.querySelectorAll<HTMLButtonElement>('.faq-chat-results button')].find(b=>b.textContent?.includes('Cómo pago'))!;
 expect(option).toBeTruthy();await act(async()=>option.click());expect(host.querySelector('[role=log] article:last-child')!.textContent).toContain('Yape o Plin');
 expect(host.querySelector('.faq-chat-body')!.lastElementChild?.getAttribute('data-chat-bottom')).toBe('true');
});
it('no fabrica respuesta ni consulta un modelo para una duda desconocida',async()=>{
 await start();await ask('astronauta galaxia');expect(api.post).not.toHaveBeenCalled();expect(host.textContent).toContain('No encontré una respuesta segura');
 expect([...host.querySelectorAll('button')].some(b=>b.textContent==='Consultar asistente de compra')).toBe(true);
});

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import { FAQ_TOPICS, searchFaq, type FaqTopic } from '../utils/faqSearch';
import { Icon } from './Icon';
import './FaqChatbot.css';

type Answer = { q:string; a:string; id:number; source?:'datos'|'ia'|'sin_respuesta'|'faq'; pending?:boolean; canAsk?:boolean; suggestions?:string[] };
interface AssistantReply { respuesta:string; tema:string; fuente:'datos'|'ia'|'sin_respuesta'; sugerencias:string[] }
const SOURCE_LABEL:Record<string,string>={datos:'Con tus datos',ia:'Con IA'};
function personal(question:string) {
 const q=question.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 return /donde.*(pedido|compra)|estado.*(pedido|compra)|cuando.*(llega|entreg)|cuanto.*(ahorr|cuesta|vale)|mi saldo|mi grupo|mi edificio/.test(q);
}
export function FaqChatbot() {
 const [open,setOpen]=useState(false),[query,setQuery]=useState(''),[lastQuery,setLastQuery]=useState('');
 const [topic,setTopic]=useState<FaqTopic>('Todas'),[history,setHistory]=useState<Answer[]>([]),[thinking,setThinking]=useState(false),[showAll,setShowAll]=useState(false);
 const asked=useRef(0),generation=useRef(0),busy=useRef(false),launcher=useRef<HTMLButtonElement>(null),search=useRef<HTMLInputElement>(null),log=useRef<HTMLDivElement>(null);
 const matches=searchFaq(query||lastQuery,topic),results=matches.slice(0,showAll?10:4);
 const close=()=>{setOpen(false);launcher.current?.focus();};
 const add=(answer:Answer)=>setHistory(current=>[...current.slice(-7),answer]);
 const askQuestion=async(text:string,forceAssistant=false)=>{
  const question=text.trim().slice(0,300);if(!question||busy.current)return;
  const id=-(++asked.current),token=generation.current;
  setQuery('');setLastQuery(question);setShowAll(false);
  if(!forceAssistant&&!personal(question)){
   const related=searchFaq(question,topic);
   add({q:question,id,source:'faq',a:related.length?'¿Tu duda está relacionada con alguna de estas opciones? Elige una para ver la respuesta.':'No encontré una respuesta segura. Prueba otro tema o consulta el asistente de compra.',canAsk:!related.length});
   return;
  }
  busy.current=true;setThinking(true);add({q:question,a:'',id,pending:true});
  const finish=(changes:Partial<Answer>)=>{if(token===generation.current)setHistory(current=>current.map(a=>a.id===id?{...a,...changes,pending:false}:a));};
  try{
   const reply=await api.post<AssistantReply>('/api/asistente',{pregunta:question});
   finish({a:reply.respuesta,source:reply.fuente,suggestions:reply.sugerencias});
  }catch(error){
   const guest=error instanceof ApiError&&(error.status===401||error.status===403);
   finish({a:guest?'Entra con tu número para preguntar por tu pedido, tu ahorro o tu entrega. Mientras, elige una pregunta frecuente.':'No pude consultar tus datos ahora. Puedes probar las preguntas frecuentes o volver a intentarlo.',source:'faq'});
  }finally{if(token===generation.current){busy.current=false;setThinking(false);}}
 };
 const submit=(event:FormEvent)=>{event.preventDefault();void askQuestion(query);};
 const reset=()=>{generation.current++;busy.current=false;setThinking(false);setHistory([]);setTopic('Todas');setQuery('');setLastQuery('');setShowAll(false);search.current?.focus();};
 useEffect(()=>()=>{generation.current++;},[]);
 useEffect(()=>{if(open)search.current?.focus();},[open]);
 useEffect(()=>{const el=log.current;if(open&&el)el.scrollTop=el.scrollHeight;},[history,thinking,open]);
 return <aside className={`faq-chat${open?' is-open':''}`} aria-label="Ayuda de Yapa">
  <button ref={launcher} type="button" className="faq-chat-launcher" aria-expanded={open} aria-controls="faq-chat-panel" onClick={()=>open?close():setOpen(true)}><span className="faq-chat-launcher-icon" aria-hidden="true"><Icon name={open?'close':'headset'} size={18}/></span><span className="faq-chat-launcher-text">¿Te ayudamos?</span></button>
  {open?<section id="faq-chat-panel" className="faq-chat-panel" role="dialog" aria-labelledby="faq-chat-title" onKeyDown={event=>{if(event.key==='Escape'){event.stopPropagation();close();}}}>
   <header className="faq-chat-header"><span className="faq-chat-avatar" aria-hidden="true"><img src="/images/brand/yapa-mark.webp" alt="" width="40" height="40"/></span><div><h2 id="faq-chat-title">Ayuda de Yapa</h2><small><i aria-hidden="true"/>Preguntas y ayuda de tu compra</small></div><button type="button" className="faq-chat-close" onClick={close} aria-label="Cerrar ayuda"><Icon name="close" size={18}/></button></header>
   <div className="faq-chat-body" ref={log}>
    <p className="faq-bubble faq-bubble--bot">Hola. Escribe tu duda y te mostraré opciones relacionadas. También puedes consultar tu pedido, entrega, ahorro o precios.</p>
    <div className="faq-chat-topics" role="group" aria-label="Temas">{FAQ_TOPICS.map(t=><button type="button" key={t} aria-pressed={topic===t} onClick={()=>{setTopic(t);setQuery('');setLastQuery('');setShowAll(false);}}>{t}</button>)}</div>
    <p className="faq-chat-count" role="status">{results.length?`${results.length} opciones relacionadas`:'No encontramos una respuesta. Prueba otro tema o revisa Mis pedidos para pagos, entregas y reclamos.'}</p>
    <ul className="faq-chat-results">{results.map(faq=><li key={faq.id}><button type="button" onClick={()=>add({...faq,source:'faq'})}>{faq.q}<Icon name="chevron" size={14}/></button></li>)}</ul>
    {matches.length>4?<button className="text-button faq-show-all" type="button" onClick={()=>setShowAll(value=>!value)}>{showAll?'Ver menos opciones':'Ver todas las preguntas'}</button>:null}
    <div className="faq-chat-history" role="log" aria-label="Respuestas" aria-live="polite">{history.map((answer,i)=><article key={`${i}-${answer.id}`}><p className="faq-bubble faq-bubble--me"><strong>{answer.q}</strong></p>{answer.a?<p className="faq-bubble faq-bubble--bot">{answer.a}{answer.source&&SOURCE_LABEL[answer.source]?<small className="faq-bubble-tag">{SOURCE_LABEL[answer.source]}</small>:null}</p>:null}
      {answer.canAsk?<button type="button" className="faq-assistant-option" disabled={thinking} onClick={()=>void askQuestion(answer.q,true)}>Consultar asistente de compra</button>:null}
      {answer.suggestions?.length?<div className="faq-chat-topics">{answer.suggestions.slice(0,5).map(q=><button type="button" disabled={thinking} key={q} onClick={()=>void askQuestion(q,true)}>{q}</button>)}</div>:null}
    </article>)}</div>
    {thinking?<p className="faq-bubble faq-bubble--bot faq-typing" aria-label="Escribiendo"><i/><i/><i/></p>:null}
    <div data-chat-bottom="true" aria-hidden="true"/>
   </div>
   <form className="faq-chat-composer" onSubmit={submit}><label><span className="sr-only">Escribe tu pregunta</span><input ref={search} type="search" value={query} maxLength={300} placeholder="Escribe tu pregunta…" onChange={event=>setQuery(event.target.value)}/></label><button className="faq-chat-send" type="submit" aria-label="Enviar pregunta" disabled={!query.trim()||thinking}><Icon name="arrow" size={18}/></button>{history.length?<button className="text-button" type="button" onClick={reset}>Reiniciar</button>:null}</form>
  </section>:null}
 </aside>;
}

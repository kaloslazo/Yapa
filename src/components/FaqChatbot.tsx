import { useEffect, useRef, useState, type FormEvent } from 'react';
import { api, ApiError } from '../services/api';
import { FAQ_TOPICS, searchFaq, type FaqTopic } from '../utils/faqSearch';
import { Icon } from './Icon';
import './FaqChatbot.css';

type Answer = { q: string; a: string; id: number; source?: 'datos' | 'ia' | 'sin_respuesta' | 'faq' };
interface AssistantReply { respuesta: string; tema: string; fuente: 'datos' | 'ia' | 'sin_respuesta'; sugerencias: string[] }
const SOURCE_LABEL: Record<string, string> = { datos: 'Con tus datos', ia: 'Con IA' };
// ayuda como chat: lo que escribes va al asistente de compra (iteración 70, con tus datos o con IA); sin sesión, las preguntas frecuentes
export function FaqChatbot() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [topic, setTopic] = useState<FaqTopic>('Todas');
  const [history, setHistory] = useState<Answer[]>([]);
  const [thinking, setThinking] = useState(false);
  const asked = useRef(0);
  const launcher = useRef<HTMLButtonElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const log = useRef<HTMLDivElement>(null);
  const results = searchFaq(query, topic);
  const close = () => { setOpen(false); launcher.current?.focus(); };
  const add = (answer: Answer) => setHistory(current => [...current.slice(-5), answer]);
  const askAssistant = async (event: FormEvent) => {
    event.preventDefault();
    const question = query.trim();
    if (!question || thinking) return;
    const id = -(++asked.current);
    setQuery('');
    setThinking(true);
    try {
      const reply = await api.post<AssistantReply>('/api/asistente', { pregunta: question });
      add({ q: question, a: reply.respuesta, id, source: reply.fuente });
    } catch (error) {
      const guest = error instanceof ApiError && (error.status === 401 || error.status === 403);
      add({ q: question, a: guest ? 'Entra con tu número para preguntar por tu pedido, tu ahorro o tu entrega. Mientras, aquí tienes las preguntas frecuentes.' : 'No pude responder ahora. Intenta en un rato o mira las preguntas frecuentes.', id, source: 'faq' });
    } finally {
      setThinking(false);
    }
  };
  useEffect(() => { if (open) search.current?.focus(); }, [open]);
  useEffect(() => { // la última respuesta queda arriba de la vista, como en un chat
    const el = log.current, last = el?.querySelector<HTMLElement>('.faq-chat-history article:last-child');
    if (el && last && typeof el.scrollTo === 'function') el.scrollTo({ top: last.offsetTop - 12, behavior: 'smooth' });
  }, [history]);
  return <aside className={`faq-chat${open ? ' is-open' : ''}`} aria-label="Ayuda de Yapa">
    <button ref={launcher} type="button" className="faq-chat-launcher" aria-expanded={open} aria-controls="faq-chat-panel" onClick={() => open ? close() : setOpen(true)}>
      <span className="faq-chat-launcher-icon" aria-hidden="true"><Icon name={open ? 'close' : 'headset'} size={18} /></span><span className="faq-chat-launcher-text">¿Te ayudamos?</span>
    </button>
    {open ? <section id="faq-chat-panel" className="faq-chat-panel" role="dialog" aria-labelledby="faq-chat-title" onKeyDown={event => { if (event.key === 'Escape') { event.stopPropagation(); close(); } }}>
      <header className="faq-chat-header">
        <span className="faq-chat-avatar" aria-hidden="true"><img src="/images/brand/yapa-mark.webp" alt="" width="40" height="40" /></span>
        <div><h2 id="faq-chat-title">Ayuda de Yapa</h2><small><i aria-hidden="true" />Respuestas al instante</small></div>
        <button type="button" className="faq-chat-close" onClick={close} aria-label="Cerrar ayuda"><Icon name="close" size={18} /></button>
      </header>
      <div className="faq-chat-body" ref={log}>
        <p className="faq-bubble faq-bubble--bot">Hola. Pregúntame por tu pedido, cuándo llega, cuánto ahorraste o el precio de un producto. También puedes elegir una pregunta frecuente.</p>
        <div className="faq-chat-history" role="log" aria-label="Respuestas" aria-live="polite">{history.map((answer, i) => <article key={`${i}-${answer.id}`}><p className="faq-bubble faq-bubble--me"><strong>{answer.q}</strong></p><p className="faq-bubble faq-bubble--bot">{answer.a}{answer.source && SOURCE_LABEL[answer.source] ? <small className="faq-bubble-tag">{SOURCE_LABEL[answer.source]}</small> : null}</p></article>)}</div>
        <div className="faq-chat-topics" role="group" aria-label="Temas">{FAQ_TOPICS.map(t => <button type="button" key={t} aria-pressed={topic === t} onClick={() => { setTopic(t); setQuery(''); }}>{t}</button>)}</div>
        <p className="faq-chat-count" role="status">{results.length ? `${results.length} preguntas sugeridas` : 'No encontramos una respuesta. Prueba otro tema o revisa Mis pedidos para pagos, entregas y reclamos.'}</p>
        {thinking ? <p className="faq-bubble faq-bubble--bot faq-typing" aria-label="Escribiendo"><i /><i /><i /></p> : null}
        <ul className="faq-chat-results">{results.map((faq, i) => <li key={faq.id} style={{ animationDelay: `${Math.min(i, 8) * 35}ms` }}><button type="button" onClick={() => add({ ...faq, source: 'faq' })}>{faq.q}<Icon name="chevron" size={14} /></button></li>)}</ul>
      </div>
      <form className="faq-chat-composer" onSubmit={event => void askAssistant(event)}>
        <label><span className="sr-only">Escribe tu pregunta</span><input ref={search} type="search" value={query} maxLength={300} placeholder="Pregunta, ej.: ¿cuándo llega mi pedido?" onChange={event => setQuery(event.target.value)} /></label>
        <button className="faq-chat-send" type="submit" aria-label="Enviar pregunta" disabled={!query.trim() || thinking}><Icon name="arrow" size={18} /></button>
        {history.length ? <button className="text-button" type="button" onClick={() => { setHistory([]); setTopic('Todas'); setQuery(''); search.current?.focus(); }}>Reiniciar</button> : null}
      </form>
    </section> : null}
  </aside>;
}

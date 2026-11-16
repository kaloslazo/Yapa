import { useEffect, useRef, useState } from 'react';
import { FAQ_TOPICS, searchFaq, type FaqTopic } from '../utils/faqSearch';
import { Icon } from './Icon';
import './FaqChatbot.css';

type Answer = { q: string; a: string; id: number };
// ayuda como chat: la pregunta elegida va a la derecha y la respuesta de las preguntas frecuentes a la izquierda
export function FaqChatbot() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [topic, setTopic] = useState<FaqTopic>('Todas');
  const [history, setHistory] = useState<Answer[]>([]);
  const launcher = useRef<HTMLButtonElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const log = useRef<HTMLDivElement>(null);
  const results = searchFaq(query, topic);
  const close = () => { setOpen(false); launcher.current?.focus(); };
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
        <p className="faq-bubble faq-bubble--bot">Hola. Elige un tema o escribe tu duda abajo. Esta ayuda no consulta ni cambia tus pedidos.</p>
        <div className="faq-chat-history" role="log" aria-label="Respuestas" aria-live="polite">{history.map((answer, i) => <article key={`${i}-${answer.id}`}><p className="faq-bubble faq-bubble--me"><strong>{answer.q}</strong></p><p className="faq-bubble faq-bubble--bot">{answer.a}</p></article>)}</div>
        <div className="faq-chat-topics" role="group" aria-label="Temas">{FAQ_TOPICS.map(t => <button type="button" key={t} aria-pressed={topic === t} onClick={() => { setTopic(t); setQuery(''); }}>{t}</button>)}</div>
        <p className="faq-chat-count" role="status">{results.length ? `${results.length} preguntas sugeridas` : 'No encontramos una respuesta. Prueba otro tema o revisa Mis pedidos para pagos, entregas y reclamos.'}</p>
        <ul className="faq-chat-results">{results.map((faq, i) => <li key={faq.id} style={{ animationDelay: `${Math.min(i, 8) * 35}ms` }}><button type="button" onClick={() => setHistory(current => [...current.slice(-5), faq])}>{faq.q}<Icon name="chevron" size={14} /></button></li>)}</ul>
      </div>
      <footer className="faq-chat-composer">
        <label><span className="sr-only">Buscar una pregunta</span><input ref={search} type="search" value={query} maxLength={300} placeholder="Escribe tu duda, ej.: no llegó mi compra" onChange={event => setQuery(event.target.value)} /></label>
        {history.length ? <button className="text-button" type="button" onClick={() => { setHistory([]); setTopic('Todas'); setQuery(''); search.current?.focus(); }}>Reiniciar</button> : null}
      </footer>
    </section> : null}
  </aside>;
}

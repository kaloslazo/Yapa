import { useEffect, useRef, useState } from 'react';
import { FAQ_TOPICS, searchFaq, type FaqTopic } from '../utils/faqSearch';
import './FaqChatbot.css';

type Answer = { q: string; a: string; id: number };
export function FaqChatbot() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [topic, setTopic] = useState<FaqTopic>('Todas');
  const [history, setHistory] = useState<Answer[]>([]);
  const launcher = useRef<HTMLButtonElement>(null);
  const search = useRef<HTMLInputElement>(null);
  const results = searchFaq(query, topic);
  const close = () => { setOpen(false); launcher.current?.focus(); };
  useEffect(() => { if (open) search.current?.focus(); }, [open]);
  return <aside className="faq-chat" aria-label="Ayuda de Yapa">
    <button ref={launcher} type="button" className="faq-chat-launcher" aria-expanded={open} aria-controls="faq-chat-panel" onClick={() => open ? close() : setOpen(true)}>¿Te ayudamos?</button>
    {open ? <section id="faq-chat-panel" className="faq-chat-panel" role="dialog" aria-labelledby="faq-chat-title" onKeyDown={event => { if (event.key === 'Escape') { event.stopPropagation(); close(); } }}>
      <header><div><h2 id="faq-chat-title">Ayuda de Yapa</h2><small>Respuestas de nuestras preguntas frecuentes</small></div><button type="button" onClick={close} aria-label="Cerrar ayuda">×</button></header>
      <p>Elige un tema o escribe tu duda. Esta ayuda no consulta ni cambia tus pedidos.</p>
      <div className="faq-chat-topics" role="group" aria-label="Temas">{FAQ_TOPICS.map(t => <button type="button" key={t} aria-pressed={topic === t} onClick={() => { setTopic(t); setQuery(''); }}>{t}</button>)}</div>
      <label>Buscar una pregunta<input ref={search} type="search" value={query} maxLength={300} placeholder="Ej.: no llegó mi compra" onChange={event => setQuery(event.target.value)} /></label>
      <p role="status">{results.length ? `${results.length} preguntas encontradas` : 'No encontramos una respuesta. Prueba otro tema o revisa Mis pedidos para pagos, entregas y reclamos.'}</p>
      <ul className="faq-chat-results">{results.map(faq => <li key={faq.id}><button type="button" onClick={() => setHistory(current => [...current.slice(-5), faq])}>{faq.q}</button></li>)}</ul>
      <div className="faq-chat-history" role="log" aria-label="Respuestas" aria-live="polite">{history.map((answer, i) => <article key={`${i}-${answer.id}`}><strong>{answer.q}</strong><p>{answer.a}</p></article>)}</div>
      {history.length ? <button className="text-button" type="button" onClick={() => { setHistory([]); setTopic('Todas'); setQuery(''); search.current?.focus(); }}>Reiniciar conversación</button> : null}
    </section> : null}
  </aside>;
}

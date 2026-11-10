import { useState } from 'react';
import type { FormEvent } from 'react';
import { api } from '../services/api';
import { toSuggestion } from '../services/mappers';
import type { BasketSuggestion } from '../types';
import { formatQuantity } from '../utils/cart';
import { formatMoney } from '../utils/format';
import { Icon } from './Icon';

interface BasketAssistantProps {
  onApply: (lines: BasketSuggestion['lines']) => void;
}

const IDEAS = ['Somos 4 y esta semana haré lomo saltado y ají de gallina', 'Vivo solo, quiero lo básico para la semana y limpiar la casa'];

// iteración 60: la IA propone y el motor pone precios, pasos y topes; el vecino decide si la agrega
export function BasketAssistant({ onApply }: BasketAssistantProps) {
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [suggestion, setSuggestion] = useState<BasketSuggestion | null>(null);

  const ask = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      setSuggestion(toSuggestion(await api.post('/api/canasta/sugerir', { texto: text })));
    } catch (problem) {
      setSuggestion(null);
      setError(problem instanceof Error ? problem.message : 'No pudimos armar la canasta. Intenta de nuevo.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="assistant-card" aria-labelledby="assistant-title">
      <div className="assistant-head">
        <span className="assistant-badge" aria-hidden="true"><Icon name="basket" size={20} /></span>
        <div><h2 id="assistant-title">Arma mi canasta</h2><p>Cuéntanos qué vas a cocinar y te proponemos productos de esta semana. Tú decides qué agregar.</p></div>
      </div>
      <form className="assistant-form" onSubmit={ask}>
        <label className="sr-only" htmlFor="assistant-text">Qué vas a cocinar esta semana</label>
        <textarea id="assistant-text" value={text} onChange={(event) => setText(event.target.value)} maxLength={300} rows={2} placeholder={IDEAS[0]} />
        <div className="assistant-actions">
          <div className="assistant-ideas">{IDEAS.map((idea) => <button key={idea} type="button" className="text-button" onClick={() => setText(idea)}>{idea.split(' ').slice(0, 4).join(' ')}…</button>)}</div>
          <button className="primary-button" type="submit" disabled={busy || text.trim().length < 3}>{busy ? 'Pensando…' : 'Proponer canasta'}</button>
        </div>
      </form>
      {error ? <p className="auth-feedback auth-feedback--error" role="alert">{error}</p> : null}
      {suggestion ? (
        <div className="assistant-result" aria-live="polite">
          {suggestion.comment ? <p className="assistant-comment">{suggestion.comment}</p> : null}
          <ul className="assistant-lines">{suggestion.lines.map((line) => <li key={line.id}><span>{line.name}</span><span>{formatQuantity(line.quantity)} {line.unit}</span><strong>{formatMoney(line.total)}</strong></li>)}</ul>
          <div className="assistant-total"><span>Subtotal (precio máximo)</span><strong>{formatMoney(suggestion.subtotal)}</strong></div>
          {suggestion.missing > 0 ? <p className="assistant-note">Te faltan {formatMoney(suggestion.missing)} para el mínimo de S/ 50: agrega algo más del catálogo.</p> : null}
          <div className="assistant-actions">
            <button className="primary-button" type="button" onClick={() => { onApply(suggestion.lines); setSuggestion(null); setText(''); }}>Agregar a mi canasta <Icon name="arrow" size={17} /></button>
            <button className="secondary-button" type="button" onClick={() => setSuggestion(null)}>Descartar</button>
          </div>
          <small className="assistant-credit">Sugerido con IA. Precios y cantidades los revisa Yapa con las reglas de siempre.</small>
        </div>
      ) : null}
    </section>
  );
}

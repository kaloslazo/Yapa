// @vitest-environment jsdom
import { act, createElement } from 'react';
import { createRoot } from 'react-dom/client';
import { describe, expect, it } from 'vitest';
import { faqs } from './EditorialSections';
import { ShoppingGuides } from './ShoppingGuides';

// guías y preguntas frecuentes al final de Explorar (rama de Aaron, ajustada al estilo de la tienda)
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true; // eslint-disable-line @typescript-eslint/no-explicit-any

const answer = (q: string) => faqs.find((f) => f.q === q)?.a ?? '';

async function render() {
  const host = document.createElement('div');
  document.body.appendChild(host);
  await act(async () => { createRoot(host).render(createElement(ShoppingGuides)); });
  return host;
}

describe('preguntas frecuentes de la tienda', () => {
  it('C-06: si el grupo no llega al mínimo se devuelve al Yape o Plin, no a saldo', () => {
    const text = answer('¿Qué pasa si mi grupo no llega al mínimo?');
    expect(text).toContain('Yape o Plin');
    expect(text).not.toContain('saldo');
  });

  it('el pago se verifica con el código que da Yapa en el mensaje, no con un código de operación', () => {
    const text = answer('¿Cómo pago mi pedido?');
    expect(text).toContain('código');
    expect(text).toContain('mensaje');
    expect(text).not.toContain('operación');
  });

  it('S-02 y S-43: el cierre del miércoles a las 8 p. m. y el reclamo dentro de 24 h', () => {
    expect(answer('¿Hasta cuándo puedo pedir?')).toContain('miércoles a las 8 p. m.');
    expect(answer('¿Qué hago si falta un producto o llegó dañado?')).toContain('24 h');
  });
});

describe('guías al final de Explorar', () => {
  it('tres guías con foto, consejos detrás de un toque y las mismas preguntas de «Cómo funciona»', async () => {
    const host = await render();
    const guides = host.querySelectorAll('.shopping-guide');
    expect(guides).toHaveLength(3);
    expect([...guides].every((g) => g.querySelector('img')?.getAttribute('src')?.startsWith('/images/products/'))).toBe(true);
    expect([...host.querySelectorAll('.shopping-guide details')].every((d) => !d.hasAttribute('open'))).toBe(true);
    expect([...host.querySelectorAll('h2')].map((h) => h.textContent)).toEqual(['Antes de pedir', 'Preguntas frecuentes']);
    expect(host.querySelectorAll('.faq-list details')).toHaveLength(faqs.length);
  });
});

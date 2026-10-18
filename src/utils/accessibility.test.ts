import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { contrast } from './contrast';
import { toastDuration } from './toast';

const css = readFileSync(new URL('../styles.css', import.meta.url), 'utf8');
const token = (name: string) => css.match(new RegExp(`--${name}:\s*(#[0-9a-fA-F]{6})`))![1];
const surfaces = ['canvas', 'page', 'paper', 'paper-strong', 'accent-soft', 'green-soft', 'yellow-soft'];

describe('AC-A · el gris de apoyo se lee en todos los fondos', () => {
  for (const surface of surfaces) {
    it(`--muted sobre --${surface} llega a 4.5`, () => expect(contrast(token('muted'), token(surface))).toBeGreaterThanOrEqual(4.5));
  }
});

describe('AC-B · el foco se ve en los fondos principales', () => {
  const ring = css.match(/:focus-visible\s*\{\s*outline:\s*\d+px solid (var\(--[a-z-]+\)|#[0-9a-fA-F]{6})/)![1];
  const color = ring.startsWith('var') ? token(ring.slice(6, -1)) : ring;
  for (const surface of ['canvas', 'page', 'paper', 'paper-strong']) {
    it(`anillo sobre --${surface} llega a 3`, () => expect(contrast(color, token(surface))).toBeGreaterThanOrEqual(3));
  }
});

describe('AC-C y AC-D · hojas de estilo', () => {
  it('ningún campo pierde el contorno de foco', () => expect(css).not.toMatch(/(input|select|textarea):focus-visible[^{]*\{\s*outline:\s*none/));
  it('la flecha de las listas usa el gris --muted', () => expect(css).toContain(`stroke='%23${token('muted').slice(1)}'`));
});

describe('AC-E · duración de los avisos', () => {
  it('éxito 6 s y advertencia 9 s', () => {
    expect(toastDuration('success')).toBe(6000);
    expect(toastDuration('warning')).toBe(9000);
  });
});

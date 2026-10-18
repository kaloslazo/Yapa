import { describe, expect, it } from 'vitest';
import { claimEffect, photoUrl } from './admin';

describe('FA-J · dirección de la foto', () => {
  it('arma la dirección con la ruta codificada', () => expect(photoUrl('fotos/aa.jpg')).toBe('/api/admin/foto?ruta=fotos%2Faa.jpg'));
  it('sin ruta no hay dirección', () => expect(photoUrl('')).toBe(''));
});

describe('FA-K · efecto de decidir un reclamo', () => {
  it('aprobar dice cuánto vuelve como saldo', () => expect(claimEffect('aprobar', 5.38)).toBe('se devuelve S/ 5.38 como saldo'));
  it('aprobar sin monto conocido no inventa cifras', () => expect(claimEffect('aprobar')).toBe('se devuelve el valor del artículo como saldo'));
  it('rechazar no devuelve nada', () => expect(claimEffect('rechazar')).toBe('no se devuelve nada'));
});

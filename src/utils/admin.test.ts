import { describe, expect, it } from 'vitest';
import { claimEffect, filterNeighbors, photoUrl } from './admin';

describe('FA-J · dirección de la foto', () => {
  it('arma la dirección con la ruta codificada', () => expect(photoUrl('fotos/aa.jpg')).toBe('/api/admin/foto?ruta=fotos%2Faa.jpg'));
  it('sin ruta no hay dirección', () => expect(photoUrl('')).toBe(''));
});

describe('FA-K · efecto de decidir un reclamo', () => {
  it('aprobar dice cuánto vuelve como saldo', () => expect(claimEffect('aprobar', 5.38)).toBe('se devuelve S/ 5.38 como saldo'));
  it('aprobar sin monto conocido no inventa cifras', () => expect(claimEffect('aprobar')).toBe('se devuelve el valor del artículo como saldo'));
  it('rechazar no devuelve nada', () => expect(claimEffect('rechazar')).toBe('no se devuelve nada'));
});

describe('FA-K · búsqueda de vecinos', () => {
  const list = [{ id: 101, nombre: 'Ana Pérez', celular: '987654321' }, { id: 105, nombre: 'Carmen Ruiz', celular: null }, { id: 230, nombre: 'Álvaro Díaz', celular: '911222333' }];
  it('sin texto devuelve todos', () => expect(filterNeighbors(list, '  ')).toHaveLength(3));
  it('busca por nombre sin importar mayúsculas ni tildes', () => expect(filterNeighbors(list, 'perez').map((v) => v.id)).toEqual([101]));
  it('busca por número de cliente', () => expect(filterNeighbors(list, '105').map((v) => v.id)).toEqual([105]));
  it('busca por celular y tolera vecinos sin celular', () => expect(filterNeighbors(list, '9112').map((v) => v.id)).toEqual([230]));
  it('sin coincidencias devuelve vacío', () => expect(filterNeighbors(list, 'zzz')).toEqual([]));
});

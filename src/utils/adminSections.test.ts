import { describe, expect, it } from 'vitest';
import { groupsOf, sectionsFor } from './adminSections';

// iteración 55: cada rol del equipo ve solo las secciones de su trabajo (CX-09)
describe('secciones del panel por rol', () => {
  const ids = (role: Parameters<typeof sectionsFor>[0]) => sectionsFor(role).map((s) => s.id);

  it('el admin ve todo el panel, sin la sección propia de atención', () => {
    expect(ids('admin')).toContain('resumen');
    expect(ids('admin')).toContain('compras');
    expect(ids('admin')).toContain('cuentas');
    expect(ids('admin')).toContain('incidencias'); // iteración 56
    expect(ids('admin')).not.toContain('pines');
  });

  it('cada rol ve solo lo suyo', () => {
    expect(ids('armador')).toEqual(['armado']);
    expect(ids('compras')).toEqual(['compras']);
    expect(ids('atencion')).toEqual(['reclamos', 'incidencias', 'devoluciones', 'pines']); // S-300
  });

  it('nadie fuera del equipo ve secciones', () => {
    for (const role of ['vecino', 'admin_zona', 'transportista', 'proveedor', 'porteria'] as const) expect(sectionsFor(role)).toEqual([]);
  });

  it('los grupos salen de las secciones visibles', () => {
    expect(groupsOf(sectionsFor('atencion'))).toEqual(['Atención']);
  });
});

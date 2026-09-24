# Resultado de aplicar SDD a Yapa

> **Documento de la iteración 1 (19/09/2026).** La versión vigente del alcance, las reglas y la evidencia está en `README.md`, `docs/sdd/10-clarificaciones-v2.md` y `docs/verification-report.md`.

## Pregunta

¿Podemos tomar una funcionalidad real del modelo de negocio de Yapa y llevarla desde una especificación hasta código verificable sin fingir que todo el proyecto está implementado?

## Alcance probado

- `CUN-02 Registrar pedido semanal`.
- Validación de las reglas RN-01, RN-02, RN-03, RN-04, RN-05, RN-07, RN-09 y RN-10.
- Contrato de salida con estado `REGISTRADO`.

## Evidencia

- El módulo está en `src/yapa_sdd/order_registration.py`.
- Las pruebas están en `tests/test_order_registration.py`.
- La suite pasa con `python -m unittest discover -s tests -v`.
- La trazabilidad está en `docs/sdd/06-trazabilidad.md`.
- Los módulos fuera de alcance están declarados en `docs/sdd/01-alcance.md`.

## Qué funcionó

- El PDF del modelado de negocio permitió seleccionar un caso de uso real, no un ejemplo inventado.
- Las reglas existentes se transformaron en validaciones concretas.
- El alcance limitado evita confundir una demo de SDD con el sistema completo.
- La revisión puede recorrer una ruta clara desde CUN-02 hasta cada test.

## Qué no se debe afirmar

- No se implementó el ciclo completo de compras y reparto.
- No se probó integración con billeteras, mapas o proveedores.
- No se resolvieron peso real, sustituciones, conciliación, devoluciones o incidencias.
- No se midió productividad frente a un flujo sin SDD.
- Las reglas económicas son supuestos académicos y no una validación del negocio real.

## Veredicto

**SDD funcionó como método de acotación, trazabilidad y validación para una vertical de Yapa.** La entrega queda defendible porque muestra qué se construyó, qué regla representa y qué permanece pendiente.


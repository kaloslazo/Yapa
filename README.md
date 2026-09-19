# Yapa · Aplicación de SDD

Repositorio académico para demostrar **Specification-Driven Development (SDD)** sobre una vertical acotada del proyecto Yapa.

## Alcance de esta entrega

Esta entrega trabaja únicamente:

- `CUN-02 Registrar pedido semanal`.
- El contrato mínimo de `CUN-03 Procesar pago`, porque CUN-02 necesita registrar el medio de pago.

Quedan fuera de este repositorio SDD: actualización del catálogo, consolidación semanal, abastecimiento mayorista, preparación de pedidos, ruteo, entregas e incidencias. Esos módulos aparecen en el repositorio general del proyecto como roadmap, pero no se presentan como implementados.

## Qué contiene

- `docs/sdd/`: contexto, alcance, especificación, plan, tareas, trazabilidad, checklist y registro de iteraciones.
- `src/yapa_sdd/`: ejemplo ejecutable de validación y registro de un pedido semanal.
- `tests/`: pruebas de los criterios de aceptación del alcance SDD.
- `docs/01-resumen-sdd-yapa.md`: resumen listo para estudiar o exponer.
- `docs/02-metodologia-sdd.md`: teoría SDD aplicada a Yapa.
- `docs/03-herramientas-2026.md`: herramientas actuales para trabajar con specs y agentes.
- `docs/05-resultados-sdd-yapa.md`: evaluación honesta de lo que funcionó.
- `docs/06-guion-presentacion-20min.md`: guion de la exposición.
- `docs/07-trazabilidad-defensa.md`: respuestas para defender requisito, regla, diseño, código y validación.
- `docs/sdd/09-prompt-para-siguiente-iteracion.md`: resumen completo y prompt para continuar iterando con SDD.
- `slides/sdd-2026-yapa-final.pptx`: presentación editable de 12 diapositivas.

## Ejecutar el ejemplo

Requiere Python 3.11 o superior.

```bash
cd sdd-2026-exposicion
PYTHONPATH=src python -m unittest discover -s tests -v
```

El código demuestra reglas de Yapa como zona piloto, ciclo activo, subtotal mínimo, tarifa de entrega, productos activos, ventana con capacidad y medios de pago permitidos.

## Evidencia SDD

La trazabilidad que se debe mostrar en la exposición es:

```text
requerimiento CUN-02
  → reglas RN-01, RN-02, RN-03, RN-04, RN-05, RN-07, RN-09 y RN-10
  → criterios de aceptación
  → diseño de dominio
  → src/yapa_sdd/order_registration.py
  → tests/test_order_registration.py
```

## Fuente funcional

El alcance se deriva de `Entregable01_ModeladoNegocio_Yapa.pdf`, compartido para esta tarea, y de las instrucciones académicas de `trabajo_sdd_tdd_diseno_software.md`. Las instrucciones del documento distinguen SDD de TDD; como este grupo tiene asignado SDD, el repositorio no desarrolla ni presenta TDD.

## Repositorio general

El mapa completo del proyecto Yapa se mantiene en un repositorio separado:

<https://github.com/kaloslazo/yapa-proyecto-completo>

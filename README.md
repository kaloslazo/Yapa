# Spec-Driven Development en 2026

Material en español para una presentación de **20 minutos como máximo** sobre Spec-Driven Development (SDD), con un ejemplo pequeño, un experimento reproducible y un flujo listo para pasarle a una IA de código.

## Qué contiene

- `docs/01-resumen-ejecutivo.md`: resumen completo para estudiar o reutilizar como briefing.
- `docs/02-metodologia-sdd.md`: teoría, conceptos, flujo, ventajas y límites.
- `docs/03-herramientas-2026.md`: mapa actualizado de herramientas y cómo escogerlas.
- `docs/specs/`: constitución, especificación, plan, tareas y checklist del ejemplo.
- `docs/prompts/`: prompts para iniciar la iteración con una IA y pedir convergencia.
- `docs/iteration-log.md`: registro de las iteraciones realizadas y de las decisiones.
- `docs/05-resultados-experimento.md`: qué funcionó, qué no y qué no se debe concluir.
- `src/focuslist/`: aplicación de ejemplo, una CLI de lista de tareas persistida en JSON.
- `tests/`: pruebas de aceptación y regresión.
- `slides/sdd-2026-exposicion-final.pptx`: presentación editable, preparada para 20 minutos.
- `docs/06-guion-presentacion-20min.md`: guion del orador con tiempos.

## Tesis de la presentación

SDD convierte la intención del producto en artefactos versionados que la IA puede interpretar, refinar y verificar. La IA acelera la implementación, pero la calidad depende de que una persona revise la especificación, las decisiones de diseño y la evidencia de prueba.

## Ejecutar el ejemplo

Requiere Python 3.11 o superior.

```bash
cd sdd-2026-exposicion
PYTHONPATH=src python -m focuslist.cli --store /tmp/focuslist-demo.json add "Preparar la presentación"
PYTHONPATH=src python -m focuslist.cli --store /tmp/focuslist-demo.json list
PYTHONPATH=src python -m focuslist.cli --store /tmp/focuslist-demo.json done 1
PYTHONPATH=src python -m focuslist.cli --store /tmp/focuslist-demo.json list --status done
```

Ejecutar las pruebas:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Flujo SDD de este repositorio

1. Leer `docs/specs/01-focuslist-spec.md`.
2. Revisar o ajustar `docs/specs/02-focuslist-plan.md`.
3. Trabajar por orden en `docs/specs/03-focuslist-tasks.md`.
4. Ejecutar la implementación y las pruebas.
5. Completar `docs/specs/04-focuslist-checklist.md`.
6. Registrar cambios en `docs/iteration-log.md`.
7. Si cambia una regla, actualizar primero la especificación, después el plan, las tareas, el código y las pruebas.

## Fuentes y corte temporal

La investigación se actualizó el **19 de septiembre de 2026**. Las fuentes primarias y el criterio de lectura están en [`docs/sources.md`](docs/sources.md).

## Nota de alcance

El experimento demuestra trazabilidad y convergencia en una aplicación pequeña. No demuestra que SDD produzca automáticamente software listo para producción ni sustituye revisión humana, pruebas de seguridad, observabilidad o diseño operativo.

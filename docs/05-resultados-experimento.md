# Resultado del experimento SDD

## Pregunta

¿Puede una IA convertir una especificación breve en una aplicación pequeña, ejecutable y verificable, manteniendo trazabilidad cuando aparece una nueva regla?

## Alcance

La aplicación `focuslist` permite crear tareas, listarlas por estado y marcarlas como completadas. Persiste en un JSON local. No se evalúan usuarios múltiples, red, seguridad, concurrencia ni despliegue.

## Procedimiento

1. Se escribió una constitución mínima.
2. Se definieron historias y criterios de aceptación.
3. Se detectaron ambigüedades antes del plan.
4. Se decidió una implementación pequeña con Python estándar.
5. Se derivaron tareas y pruebas.
6. Se implementó la primera versión.
7. Se añadió una petición nueva: listar por estado y hacer idempotente `done`.
8. Se actualizó primero la spec, luego el plan, tareas, código y tests.
9. Se ejecutó la suite completa y se revisaron los criterios.

## Evidencia observada

- La implementación se puede ejecutar sin dependencias externas.
- La suite final contiene 7 pruebas y pasa con `python -m unittest discover -s tests -v`.
- La nueva regla sobre `done` descubrió un caso que no estaba cerrado en la primera versión.
- El registro de iteración permite ver qué cambió y por qué.
- El código conserva decisiones pequeñas y visibles: JSON legible, IDs incrementales y filtros explícitos.

## Qué funcionó

- La spec acotó el comportamiento y evitó inventar funciones no solicitadas.
- Los criterios de aceptación se tradujeron directamente en tests.
- Separar spec, plan y tareas hizo más fácil decidir qué documento modificar ante un cambio.
- La convergencia final encontró que los artefactos, el código y las pruebas estaban alineados para el alcance definido.

## Qué no funcionó o no se puede afirmar

- No se puede afirmar que la IA produzca software de producción sin revisión.
- No se midió tiempo comparado con un flujo sin SDD, por lo que no hay conclusión de productividad.
- Un JSON local no resuelve concurrencia, corrupción, migraciones ni backup.
- La lista de tareas no captura por sí sola riesgos operativos ni requisitos no funcionales ausentes.
- Un criterio de aceptación mal escrito habría producido tests igualmente pobres.

## Veredicto

**Funcionó como método de reducción de ambigüedad y trazabilidad en una aplicación pequeña.** La evidencia es suficiente para defender el proceso en una charla y como piloto interno. No es suficiente para generalizar que SDD siempre acelera o garantiza calidad.

## Próximo experimento recomendado

Repetir la misma funcionalidad con tres condiciones: prompt directo sin artefactos, spec-anchored con revisión humana y spec-as-source con contratos. Medir tiempo hasta primera versión útil, cambios posteriores, defectos encontrados y coste de mantener la documentación.


# Registro de iteraciones

## Iteración 0 — intención inicial

Entrada a la IA: “Construye una aplicación pequeña para gestionar tareas. Debe permitir crear, listar y completar tareas.”

### Ambigüedades detectadas

- ¿Dónde se guardan los datos?
- ¿Qué formato tiene una tarea?
- ¿Qué ocurre con título vacío o demasiado largo?
- ¿Qué pasa si se completa dos veces la misma tarea?
- ¿Cómo se identifican las tareas?
- ¿Cuál es el alcance que queda fuera?

La IA no debe rellenar estas respuestas silenciosamente cuando afectan al comportamiento. Se resolvieron en la spec antes de implementar.

## Iteración 1 — especificación aprobada

Se definió `docs/specs/01-focuslist-spec.md` con JSON local, IDs incrementales, título máximo de 80 caracteres, filtros `all/open/done`, acción `done` idempotente y errores legibles.

Resultado: la spec se puede convertir en pruebas sin preguntar qué significa “completo”.

## Iteración 2 — plan y tareas

Se eligió Python 3.11 + biblioteca estándar para que la demo sea portable. Se derivaron tareas de dominio, persistencia, CLI y pruebas. Cada tarea referencia una regla o criterio.

## Iteración 3 — primera implementación

Se implementaron `add`, `list` y `done`, con persistencia atómica mediante archivo temporal. Las pruebas cubren entradas, filtros, idempotencia, error de ID y formato JSON.

## Iteración 4 — cambio de producto

Petición: “Necesito listar solo abiertas o completadas y que repetir `done` no rompa nada”.

Orden aplicado:

1. Actualizar criterios de aceptación.
2. Actualizar plan y tareas.
3. Implementar filtros e idempotencia.
4. Agregar pruebas de regresión.
5. Ejecutar la suite.
6. Revisar la convergencia.

## Resultado

La suite final pasa con 7 pruebas. La nueva petición modificó la spec y dejó evidencia de por qué existe el comportamiento idempotente. El proceso funcionó para el alcance de demo y dejó claras sus limitaciones de producción.


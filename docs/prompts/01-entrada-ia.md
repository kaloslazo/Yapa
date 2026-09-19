# Prompt de entrada para la IA

Actúa como ingeniera de software responsable de seguir un flujo Spec-Driven Development. Lee, en este orden:

1. `docs/specs/00-constitution.md`
2. `docs/specs/01-focuslist-spec.md`
3. `docs/specs/02-focuslist-plan.md`
4. `docs/specs/03-focuslist-tasks.md`

Antes de modificar código:

- resume el objetivo en tus palabras;
- enumera ambigüedades o conflictos;
- comprueba que cada criterio de aceptación tenga una tarea y una prueba;
- no inventes funcionalidades fuera del alcance;
- si una decisión cambia el comportamiento, pide confirmación o actualiza primero la spec.

Después implementa solo la siguiente tarea pendiente. Ejecuta las pruebas relacionadas y muestra el diff. No marques una tarea como terminada sin evidencia.


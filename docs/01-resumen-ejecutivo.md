# SDD en una página

## Definición

**Spec-Driven Development (SDD)** es una forma de construir software en la que una especificación versionada conserva la intención del producto y guía el trabajo de la IA de código. La especificación describe el comportamiento observable, las restricciones y los criterios de aceptación; después se deriva un plan técnico, una lista de tareas, la implementación y la evidencia de verificación.

En 2026 conviven dos usos del término:

1. **SDD clásico o de alta formalidad**: la especificación puede ser un contrato, un modelo o una notación verificable.
2. **SDD agentic o AI-native**: documentos Markdown estructurados funcionan como contexto persistente para un agente que propone diseño y código, con revisión humana entre etapas.

El segundo uso es el que popularizaron GitHub Spec Kit y Kiro. No significa que la IA genere producción desde un único documento perfecto; significa que el equipo conserva una cadena de intención, decisiones, tareas y pruebas.

## La idea central

```text
intención del producto
        ↓
especificación verificable
        ↓
plan técnico y decisiones
        ↓
tareas trazables
        ↓
código + pruebas
        ↓
convergencia contra la especificación
```

Si cambia una regla de negocio, primero cambia la especificación. Luego se regeneran o corrigen el plan, las tareas, el código y las pruebas. Así se reduce el problema de que el código evolucione mientras la documentación queda obsoleta.

## Qué debe contener una buena especificación

- Problema y usuarios afectados.
- Alcance y fuera de alcance.
- Historias de usuario o escenarios.
- Reglas de negocio expresadas sin ambigüedad.
- Criterios de aceptación observables.
- Errores y casos límite.
- Restricciones no funcionales: seguridad, rendimiento, disponibilidad, privacidad y compatibilidad.
- Datos, interfaces y decisiones que sí deben permanecer estables.
- Preguntas abiertas y supuestos pendientes de validar.

Una buena regla de aceptación se puede probar. Ejemplo: “Cuando una persona crea una tarea con título vacío, el sistema rechaza la operación y muestra un error legible”.

## Flujo práctico en 2026

El flujo más visible del ecosistema es:

1. **Constitución**: principios, arquitectura permitida, versiones, estándares y límites.
2. **Specify**: requisitos, escenarios y aceptación.
3. **Clarify**: resolver ambigüedades antes de diseñar.
4. **Plan**: arquitectura, datos, interfaces y decisiones técnicas.
5. **Checklist / analyze**: revisar calidad y consistencia de los artefactos.
6. **Tasks**: dividir el plan en tareas pequeñas y ordenadas.
7. **Implement**: ejecutar tareas con la IA, revisando diffs y pruebas.
8. **Converge**: comparar la implementación contra los artefactos y registrar trabajo restante.

GitHub Spec Kit documenta estos comandos como `/speckit.constitution`, `/speckit.specify`, `/speckit.clarify`, `/speckit.plan`, `/speckit.checklist`, `/speckit.tasks`, `/speckit.analyze`, `/speckit.implement` y `/speckit.converge`. No todas las fases son obligatorias en todos los cambios; la rigurosidad debe seguir al riesgo.

## Herramientas relevantes

- **GitHub Spec Kit**: toolkit abierto con plantillas, comandos y múltiples integraciones de agentes. Es la referencia más visible para el flujo `specify → plan → tasks → implement → converge`.
- **Kiro**: IDE, CLI y web con specs divididas en `requirements.md`, `design.md` y `tasks.md`; permite refinar requisitos y sincronizar tareas.
- **Tessl**: specs Markdown vinculadas a pruebas y un registro de conocimiento de librerías y skills.
- **Agentes de código**: GitHub Copilot, Codex, Claude Code, Gemini CLI, Kiro, Zed y otros. El agente ejecuta la metodología; no define por sí solo la calidad del proceso.
- **Verificación**: unittest o pytest, linters, type checkers, contract tests, CI, revisión de diff y análisis de seguridad.
- **Control de cambios**: Git, pull requests, issues y revisión humana de los artefactos junto con el código.

## ¿Ha funcionado?

En el ejemplo de este repositorio, sí funcionó para el objetivo acotado: una CLI de tareas pasó de una especificación a una implementación ejecutable con 7 pruebas, criterios de aceptación cubiertos y un registro de iteración. La trazabilidad hizo visible una ambigüedad importante: qué significa volver a completar una tarea; la especificación decidió que la operación sea idempotente.

Eso no prueba que SDD haga automáticamente software listo para producción. El experimento no cubre concurrencia, usuarios múltiples, autenticación, migraciones, rendimiento, observabilidad ni seguridad. El resultado defendible es más modesto: **SDD redujo la ambigüedad y facilitó la revisión en este alcance pequeño; no reemplazó el juicio de ingeniería**.

## Cómo aplicaría SDD y TDD en mi trabajo

Aplicaría **SDD para ordenar la intención** y **TDD para construir cada tarea con feedback rápido**:

1. Convertiría la necesidad del usuario en una spec con escenarios y criterios de aceptación.
2. Revisaría la spec con el equipo antes de diseñar.
3. Dividiría cada historia en tareas pequeñas.
4. Para cada tarea escribiría primero una prueba que represente el criterio pendiente.
5. Implementaría el cambio mínimo para pasarla y después refactorizaría sin alterar el comportamiento.
6. Ejecutaría la suite completa y actualizaría la spec si aparece una decisión nueva.

Así, SDD responde “qué debe cumplirse” y TDD mantiene el ciclo de construcción corto: prueba que falla, implementación mínima, prueba que pasa y refactor.

## Cuándo usarlo

Usarlo cuando la funcionalidad tiene reglas, varios casos límite, más de una persona o agente, requisitos de cumplimiento, una base de código grande o riesgo de regresión.

Usar un flujo más ligero cuando el cambio es una corrección trivial, un experimento descartable o una exploración cuyo objetivo aún no está claro.

## Mensaje final

La IA escribe más rápido cuando recibe contexto claro. SDD convierte ese contexto en un activo del repositorio. El beneficio no viene de escribir más Markdown, sino de mantener una relación verificable entre intención, decisión, tarea, código y prueba.

# Herramientas de SDD para código en 2026

## Mapa rápido

| Capa | Herramientas / ejemplos | Uso | Observación |
| --- | --- | --- | --- |
| Método y plantillas | GitHub Spec Kit | `constitution → specify → plan → tasks → implement → converge` | Abierto, integrable con varios agentes; requiere adaptar plantillas al equipo |
| IDE / agente con specs | Kiro | `requirements.md`, `design.md`, `tasks.md`; refinamiento y sincronización | Buen encaje si el equipo quiere un entorno guiado |
| Especificación y conocimiento de librerías | Tessl | `.spec.md`, enlaces a tests y registry de skills | Útil cuando el agente necesita contexto versionado de dependencias |
| Agentes de código | GitHub Copilot, Codex, Claude Code, Gemini CLI, Kiro, Zed y otros | Interpretan artefactos y ejecutan tareas | La metodología es más importante que la marca del agente |
| Verificación | pytest / unittest, linters, mypy o pyright, contract tests, CI | Comprueban criterios y regresiones | Los tests prueban comportamiento, no sustituyen revisión de requisitos |
| Gestión de cambios | Git, pull requests, issues | Versionan spec, código y evidencia | Un cambio de requisito debe dejar rastro |
| Calidad de artefactos | checklists, análisis de consistencia, revisión humana | Encuentran requisitos faltantes o contradictorios | No dejar al mismo agente autoaprobar todo |

## GitHub Spec Kit

La documentación oficial de septiembre de 2026 presenta el núcleo como un proceso que lleva una especificación por planificación, implementación y convergencia. Se inicializa con `specify init`; la página oficial muestra integración con distintos agentes y una salida de escape `generic`.

Comandos representativos:

```text
/speckit.constitution
/speckit.specify
/speckit.clarify
/speckit.plan
/speckit.checklist
/speckit.tasks
/speckit.analyze
/speckit.implement
/speckit.converge
```

No hay que ejecutar toda la cadena para cada typo. El nivel de control debe corresponder al riesgo, la novedad y la cantidad de decisiones.

## Kiro

Kiro presenta specs como documentos de requisitos, diseño y tareas. Su documentación describe dos entradas: Requirements-First cuando se conoce el comportamiento y la arquitectura aún es flexible; Design-First cuando ya existe una arquitectura o hay restricciones técnicas fuertes. También documenta cómo importar requisitos existentes y sincronizar cambios hacia diseño y tareas.

## Tessl

Tessl representa specs como parte versionada del proyecto y propone enlazarlas con tests. Su registry añade contexto de uso para librerías y paquetes. Es una dirección interesante cuando el riesgo principal es que el agente use una API incorrecta o una versión incompatible.

## Qué usar en el ejemplo

El ejemplo de este repositorio usa solo archivos Markdown + Git + Python `unittest`. Esa elección es intencional:

- deja visible el método sin exigir una herramienta propietaria;
- permite reproducir la demo con cualquier agente;
- hace explícita la diferencia entre **metodología** y **automatización del flujo**.

El mismo conjunto de artefactos puede migrar después a Spec Kit, Kiro u otra integración. La migración no debe cambiar las reglas del producto; solo el envoltorio del proceso.

## Cómo escoger

Elegir por:

1. **Compatibilidad con el agente y el repositorio**: comandos, skills, CLI, monorepo y brownfield.
2. **Persistencia**: dónde viven las specs, cómo se versionan y cómo se enlazan con PRs.
3. **Calidad**: checklists, análisis de consistencia, tests y revisión humana.
4. **Privacidad y operación**: modelo, telemetría, secretos, ejecución local o nube.
5. **Fricción**: si el flujo produce más artefactos de los que el equipo puede mantener, hay que simplificarlo.


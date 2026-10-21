# Herramientas de SDD para código en 2026

| Capa | Herramientas | Uso en SDD |
| --- | --- | --- |
| Flujo y plantillas | GitHub Spec Kit | constitution, specify, plan, tasks, implement y converge |
| IDE y agente | Kiro | requirements, design y tasks con refinamiento |
| Specs y contexto de librerías | Tessl | specs Markdown, enlaces a tests y registry |
| Agentes de código | Copilot, Codex, Claude Code, Gemini CLI, Kiro y otros | leer artefactos y ejecutar tareas |
| Verificación | unittest, pytest, linters, type checkers, CI | demostrar criterios y regresiones |
| Control de cambios | Git, pull requests, issues | versionar spec, código y evidencia |

## Qué usamos en esta entrega

Usamos Markdown versionado, Git, Python estándar y `unittest`. La decisión mantiene visible el método y no ata la exposición a una herramienta específica. Los mismos artefactos pueden migrar luego a GitHub Spec Kit, Kiro u otra integración.

## Criterio de elección

Elegir por compatibilidad con el repositorio, persistencia de las specs, privacidad del código, calidad de los gates y coste de mantenimiento. Una herramienta que genera muchos documentos sin mejorar las decisiones agrega fricción.

## Fuentes actuales

- GitHub Spec Kit: <https://github.github.com/spec-kit/>
- Agentic SDD: <https://github.github.com/spec-kit/reference/agentic-sdd.html>
- Kiro Specs: <https://kiro.dev/docs/specs/best-practices/>
- Tessl SDD: <https://tessl.io/registry/tessl-labs/spec-driven-development/2.0.1/files/docs/index.md>


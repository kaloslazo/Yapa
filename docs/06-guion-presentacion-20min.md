# Guion para una presentación de 20 minutos

La presentación tiene 12 diapositivas. El ritmo objetivo es de 17 a 19 minutos, dejando margen para una pregunta.

| Tiempo | Diapositiva | Mensaje |
| ---: | --- | --- |
| 0:45 | 1. Portada | SDD organiza la colaboración con una IA alrededor de intención y evidencia |
| 1:30 | 2. Por qué aparece ahora | Los agentes pueden escribir código, pero pierden contexto y supuestos |
| 2:00 | 3. Qué es SDD | La spec es un artefacto vivo, versionado y verificable |
| 2:00 | 4. Cadena de artefactos | Constitución, spec, plan, tareas, código, pruebas, convergencia |
| 2:00 | 5. Flujo de trabajo | Aclarar antes de planificar; revisar después de implementar |
| 1:45 | 6. Aplicación SDD + TDD | Cómo lo usaría en mi trabajo |
| 1:45 | 7. Herramientas 2026 | Spec Kit, Kiro, Tessl y agentes de código |
| 1:45 | 8. Ejemplo FocusList | Qué se pidió y qué documentos recibió la IA |
| 2:30 | 9. Iteración + código | La nueva regla actualiza spec, plan, tareas, código y tests |
| 1:45 | 10. Evidencia | 7 pruebas, ejecución reproducible, límites explícitos |
| 1:30 | 11. Dónde falla | Context rot, burocracia, falsa precisión y revisión pendiente |
| 0:45 | 12. Cierre | Empezar pequeño, medir y mantener la cadena de trazabilidad |

## Apertura sugerida

“En 2026 el problema ya no es solo cuánto código puede escribir un agente. El problema es si entiende qué debía construir, qué decisiones puede tomar y cómo sabemos que terminó. SDD responde con artefactos persistentes.”

## Demo verbal

Mostrar la relación:

```text
spec.md → plan.md → tasks.md → src/ + tests/ → converge
```

Explicar que `focuslist` empezó con reglas pequeñas. La IA no recibió un “haz una app” sin contexto: recibió comportamiento, límites, errores y criterios. Después se agregó un cambio real: filtrar por estado y hacer idempotente la acción `done`. Mostrar el test de doble `done` como el ejemplo TDD.

## Cierre sugerido

“El resultado no es magia ni automatización total. SDD funciona cuando mantiene sincronizados intención, decisión, implementación y prueba. Si el equipo no revisa la spec o la deja crecer sin control, el proceso solo documenta los errores más rápido.”

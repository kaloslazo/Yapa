# Metodología SDD para desarrollo de software

## 1. SDD no es un único estándar

La expresión “Spec-Driven Development” se usa para prácticas con distintos grados de formalidad. En común tienen una idea: la especificación deja de ser un documento que se desecha después del análisis y pasa a ser un artefacto que orienta la construcción y la verificación.

En el SDD contemporáneo impulsado por agentes, la especificación suele ser texto estructurado. El lenguaje natural mantiene la conversación con producto y negocio; el formato, los criterios de aceptación y los enlaces a pruebas hacen que ese texto sea accionable.

## 2. Niveles de rigor

Una adopción gradual evita convertir cada cambio en burocracia:

### Spec-first

La persona escribe el comportamiento esperado antes de pedir código. La IA genera una primera implementación y pruebas. Es adecuado para tareas pequeñas, prototipos y equipos que están aprendiendo.

### Spec-anchored

La especificación se versiona junto al código, se revisa en pull request y contiene criterios de aceptación y decisiones técnicas. Las pruebas comprueban los criterios importantes. Es un buen nivel por defecto para funcionalidades de producto.

### Spec-as-source

La especificación es la fuente de verdad de la que se generan código, tests, contratos o configuraciones, con validación automática. Se justifica cuando la consistencia tiene mucho valor: APIs públicas, sistemas regulados, integraciones críticas o código generado repetidamente.

No todas las partes de un sistema necesitan el mismo nivel. Un módulo crítico puede requerir contratos y pruebas de propiedades; un script interno puede quedarse en spec-first.

## 3. Artefactos y responsabilidades

| Artefacto | Pregunta que responde | Revisión principal |
| --- | --- | --- |
| Constitución | ¿Qué principios y límites no deben romperse? | Ingeniería / arquitectura |
| Especificación | ¿Qué debe ocurrir para cada escenario? | Producto + ingeniería |
| Plan | ¿Cómo lo implementaremos y por qué? | Ingeniería |
| Tareas | ¿Qué cambio concreto hacemos y en qué orden? | Implementación |
| Código | ¿Qué comportamiento ejecuta el sistema? | Revisión de diff |
| Pruebas | ¿Qué evidencia tenemos de que cumple? | CI + revisión |
| Convergencia | ¿Qué quedó desalineado o pendiente? | Dueño de la funcionalidad |

La IA puede redactar todos estos documentos, pero no debería autoaprobar los criterios que ella misma generó. La aceptación de requisitos y la aprobación de riesgos necesitan una persona responsable.

## 4. Cómo se escribe una spec útil

### A. Separar comportamiento de implementación

Primero: “La persona puede filtrar tareas por estado”. Después, si hace falta: “la implementación usa un archivo JSON local”. El primer enunciado protege la intención; el segundo fija una decisión técnica.

### B. Convertir adjetivos en reglas

“La interfaz debe ser rápida” no se puede comprobar sin una métrica. Es mejor: “El comando local responde en menos de 200 ms con 1.000 tareas en un entorno de desarrollo de referencia”.

### C. Especificar lo incómodo

La calidad de una spec aparece en las preguntas que evita: entrada vacía, duplicados, permisos, datos corruptos, reintentos, desconexión, zona horaria, límites, eliminación, reanudación y compatibilidad.

### D. Escribir aceptación como prueba

Una forma legible es:

```text
WHEN <condición>
THE SYSTEM SHALL <resultado observable>
```

También se puede usar Given / When / Then cuando el equipo ya trabaja con BDD. El formato importa menos que la observabilidad y la trazabilidad.

## 5. Iteración correcta

El error típico es pedir “implementa todo” y aceptar la primera salida. Un ciclo sano es:

1. La IA reformula la intención y enumera dudas.
2. La persona responde o decide supuestos.
3. La IA propone la spec.
4. La persona aprueba alcance y aceptación.
5. La IA propone plan y tareas pequeñas.
6. La IA implementa una tarea o una historia a la vez.
7. Se ejecutan pruebas y se inspecciona el diff.
8. La IA compara código y spec, registra gaps y propone la siguiente iteración.

Cada iteración debe cambiar algo identificable: una regla, una decisión, un test, una tarea o una corrección. “Iterar” no es pedir más texto; es cerrar incertidumbre con evidencia.

## 6. Beneficios esperables

- Menos supuestos ocultos dentro del prompt.
- Mejor memoria entre sesiones y agentes.
- Revisiones más concretas porque el diff incluye intención y código.
- Tareas más pequeñas y paralelizables.
- Mayor facilidad para detectar una funcionalidad sin criterio de aceptación.
- Mejor trazabilidad en equipos y dominios regulados.

## 7. Costes y fallos frecuentes

- **Especificación inflada**: demasiadas instrucciones consumen contexto y pueden producir “context rot”.
- **Falsa precisión**: una frase bien formateada sigue siendo incorrecta si el negocio no la validó.
- **Desalineación**: el código cambia y la spec no; el repositorio conserva una historia falsa.
- **Defensividad innecesaria**: la IA agrega validaciones o abstracciones que la spec no pide.
- **Bucle de documentación**: el equipo optimiza Markdown y posterga pruebas o entrega.
- **Sobreconfianza en tests**: pasar pruebas no demuestra seguridad, escalabilidad ni valor de producto.
- **Contexto insuficiente**: en brownfield, la IA puede inventar APIs si no inspecciona el repositorio real.

## 8. SDD y prácticas vecinas

- **TDD** empieza desde una prueba que falla y guía el diseño del código. SDD empieza desde la intención y puede derivar pruebas; se complementan.
- **BDD** expresa comportamiento desde el punto de vista del usuario. Sus escenarios pueden formar parte de la spec SDD.
- **Design by Contract** formaliza precondiciones, postcondiciones e invariantes. Es útil para subir el rigor de la spec.
- **Contract-Driven Development** acuerda obligaciones observables entre servicios o consumidores, especialmente cuando hay interfaces externas.
- **Documentación tradicional** explica el sistema, pero no siempre impone una cadena de ejecución y verificación.

## 9. Criterio de adopción

Adoptar SDD cuando el coste de una mala interpretación sea mayor que el coste de mantener los artefactos. Empezar con una sola funcionalidad, medir retrabajo y defectos encontrados antes de producción, y simplificar las plantillas que no aporten decisiones.


# Metodología SDD aplicada a Yapa

## Definición

Specification-Driven Development usa especificaciones versionadas para dirigir decisiones de diseño, implementación y validación. La especificación conserva la intención del negocio y permite revisar si el código representa esa intención.

## Flujo de trabajo

1. Identificar la necesidad del usuario.
2. Separar alcance incluido y excluido.
3. Transformar requisitos en especificaciones observables.
4. Declarar reglas de negocio y criterios de aceptación.
5. Diseñar el módulo que satisface esos criterios.
6. Implementar una tarea pequeña.
7. Validar el resultado contra la especificación.
8. Registrar gaps y actualizar los artefactos si cambia una regla.

## Aplicación concreta

En Yapa, el requisito “el cliente puede registrar un pedido semanal” es insuficiente por sí solo. La spec agrega zona, ciclo, subtotal, tarifa, vigencia, capacidad y medio de pago. Cada decisión se puede relacionar con una regla existente del modelado de negocio.

## Artefactos

| Artefacto | En Yapa |
| --- | --- |
| Contexto | negocio de compras mayoristas por zona |
| Alcance | CUN-02 y contrato mínimo de CUN-03 |
| Especificación | entradas, reglas, escenarios y errores |
| Plan | dominio, validaciones y contrato de salida |
| Tareas | cambios ordenados por criterio |
| Implementación | módulo `order_registration.py` |
| Evidencia | pruebas y ejecución reproducible |
| Convergencia | comparación entre spec, código y pruebas |

## Puntos clave para manejar SDD

- La spec debe preceder al código del alcance que se quiere defender.
- Cada regla importante debe tener una forma de verificación.
- La IA puede proponer documentos y código, pero una persona debe aprobar la interpretación del negocio.
- El alcance debe declarar qué módulos no se implementan.
- No se debe esconder una decisión nueva únicamente en el código.
- Una modificación de requisito actualiza spec, plan, tareas, código y pruebas en ese orden.
- Los artefactos deben vivir en Git junto al código.
- Una checklist revisa la calidad de la spec; las pruebas revisan el comportamiento implementado.

## Ventajas

- Reduce ambigüedad entre negocio y desarrollo.
- Evita presentar como terminado un módulo que solo tiene código parcial.
- Hace visible la relación entre regla y validación.
- Conserva decisiones para futuras iteraciones del proyecto.

## Limitaciones

- Una spec incorrecta puede producir código coherente pero equivocado.
- Mantener demasiadas instrucciones puede generar contexto innecesario.
- Pasar pruebas no demuestra viabilidad comercial, seguridad, rendimiento o experiencia de usuario.
- Las reglas del PDF son supuestos académicos hasta que el equipo las valide con el negocio.


# Guion de exposición SDD sobre Yapa

> **Documento de la iteración 1 (19/09/2026).** La versión vigente del alcance, las reglas y la evidencia está en `README.md`, `docs/sdd/10-clarificaciones-v2.md` y `docs/verification-report.md`.

La presentación tiene 12 diapositivas y un ritmo objetivo de 17 a 19 minutos.

| Tiempo | Diapositiva | Mensaje |
| ---: | --- | --- |
| 0:45 | 1. Portada | SDD aplicado a una vertical real de Yapa |
| 1:15 | 2. Problema | El ciclo semanal necesita reglas y trazabilidad |
| 1:30 | 3. Definición | La spec dirige diseño, código y validación |
| 1:30 | 4. Cadena | Requisito, regla, criterio, diseño, código y resultado |
| 1:30 | 5. Flujo | Aclarar, especificar, diseñar, implementar y validar |
| 1:30 | 6. Aplicación a Yapa | Qué se incluye y qué se excluye |
| 1:30 | 7. Herramientas | Markdown, Git, agentes y verificación |
| 1:30 | 8. Caso CUN-02 | Registrar pedido semanal |
| 2:30 | 9. Código | Mostrar una validación y su criterio |
| 1:30 | 10. Evidencia | Pruebas y trazabilidad |
| 1:30 | 11. Límites | No confundir vertical demostrada con sistema completo |
| 0:45 | 12. Cierre | SDD deja una base segura para los siguientes módulos |

## Apertura

“Yapa no necesita solo una pantalla de pedidos. Tiene zonas, cierres de ciclo, montos mínimos, ventanas de entrega y medios de pago. SDD nos ayuda a convertir esas reglas del negocio en una implementación que podemos defender.”

## Demo

1. Abrir `docs/sdd/02-especificacion-cun-02.md`.
2. Mostrar RN-01, RN-03 y RN-04.
3. Abrir `src/yapa_sdd/order_registration.py`.
4. Ejecutar la suite de pruebas.
5. Mostrar un caso válido y un caso rechazado por subtotal o zona.
6. Explicar qué módulos todavía no se implementan.

## Cierre

“La evidencia no dice que Yapa esté terminado. Dice algo más preciso: esta vertical cumple los criterios que especificamos y deja trazado qué debe construirse después.”


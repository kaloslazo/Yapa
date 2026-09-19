# Paquete de arranque para la siguiente iteración

Este archivo es el resumen operativo que se puede entregar a otra IA para continuar el proyecto con SDD. La IA debe leer los artefactos en el orden indicado y no saltar directamente al código.

## Orden de lectura

1. `docs/sdd/00-contexto-yapa.md`
2. `docs/sdd/01-alcance.md`
3. `docs/sdd/02-especificacion-cun-02.md`
4. `docs/sdd/03-plan.md`
5. `docs/sdd/04-tareas.md`
6. `docs/sdd/05-criterios-aceptacion.md`
7. `docs/sdd/06-trazabilidad.md`
8. `docs/sdd/07-checklist-convergencia.md`
9. `docs/sdd/08-registro-iteraciones.md`

## Resumen que la IA debe conservar

- Producto: Yapa, compras mayoristas consolidadas por zona.
- Entrega académica: solo SDD; no introducir una narrativa o módulo de otra metodología.
- Vertical actual: `CUN-02 Registrar pedido semanal`.
- Límite funcional: guardar el medio de pago permitido, sin conciliar pagos externos.
- Distritos piloto: Lince, Jesús María y La Victoria.
- Ventana de registro: lunes 00:00 a miércoles 20:00.
- Subtotal mínimo: S/ 50.00.
- Delivery: S/ 7.90; gratuito desde S/ 120.00.
- Requisitos de la orden: producto activo, precio con unidad y vigencia, dirección validada, ventana con capacidad y medio de pago permitido.
- Estado válido de salida: `REGISTRADO`.
- Fuera de alcance: persistencia, web, autenticación, pagos externos, mapas, consolidación, compra, preparación, entrega e incidencias.

## Instrucción para iniciar una iteración

```text
Actúa como agente de desarrollo guiado por especificaciones para el proyecto Yapa.

Lee primero, en orden, todos los archivos de docs/sdd indicados en
docs/sdd/09-prompt-para-siguiente-iteracion.md. No inventes reglas de negocio
ni implementes módulos fuera de alcance.

Antes de modificar código:
1. resume el requisito que entendiste;
2. identifica las reglas y criterios afectados;
3. declara ambigüedades y supuestos;
4. propone cambios concretos a la especificación, el plan y las tareas;
5. propone pruebas de aceptación y una matriz de trazabilidad actualizada.

Solo después de esa revisión implementa el cambio mínimo. Actualiza primero
los artefactos SDD y luego src/ y tests/. Ejecuta la suite, revisa el diff y
termina con: cambios realizados, evidencia, riesgos, pendientes y módulos que
siguen fuera de alcance.
```

## Siguiente incremento recomendado

No ampliar CUN-02 por comodidad. El siguiente incremento del proyecto general es especificar y separar `CUN-03 Procesar pago`: estados de pago, verificación de transferencia hasta el jueves 12:00, unicidad de referencia y límites de integración. Ese trabajo debe abrirse como una nueva especificación antes de programarse.

# Guía de defensa SDD

## ¿Qué parte del proyecto implementaron?

Implementamos una vertical acotada de Yapa: registrar un pedido semanal, con las validaciones de zona, ciclo, subtotal, tarifa, vigencia, disponibilidad de ventana y medio de pago. El resto del ciclo semanal queda fuera de esta entrega.

## ¿Dónde está la especificación?

En `docs/sdd/02-especificacion-cun-02.md`. Ahí aparecen entradas, reglas, criterios de aceptación, errores y salida esperada.

## ¿Qué regla se ve en el código?

RN-03 exige un subtotal mínimo de S/ 50 y RN-04 define la tarifa de S/ 7.90, exonerada desde S/ 120. Ambas aparecen en `register_weekly_order` y tienen pruebas.

## ¿Cómo saben que cumple?

Cada criterio tiene una prueba en `tests/test_order_registration.py`. La suite se ejecuta desde un checkout limpio y el resultado queda registrado en el README.

## ¿Qué pasa si cambia la especificación?

Se actualiza primero la spec, luego el plan y las tareas, después el código y las pruebas. La diferencia queda en Git y en `docs/sdd/08-registro-iteraciones.md`.

## ¿Por qué no implementaron todo?

Porque el profesor pide aplicar la metodología sobre una funcionalidad con lógica de negocio. Implementar CUN-01 a CUN-08 en una sola entrega ocultaría qué parte fue realmente dirigida por SDD. El repositorio general conserva el mapa completo para continuar después.


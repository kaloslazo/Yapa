# Guía de defensa SDD (iteración 2)

## ¿Qué parte del proyecto implementaron?

Dos funcionalidades con lógica de negocio real:

1. **Registrar pedido semanal**, con precio máximo garantizado y pago anticipado por Yape o Plin.
2. **Liquidar el ciclo** ("te devolvemos"): el ahorro del grupo, el envío compartido y los faltantes vuelven como saldo a favor.

## ¿Qué diferencia hay entre requisito y especificación?

El **requisito** es la necesidad: *"quiero registrar mi pedido y no pagar de más"*.

La **especificación** la vuelve verificable:
- entradas y salidas en JSON;
- reglas RP-01..RP-15 con su orden;
- 15 códigos de error;
- valores concretos: S/ 50, S/ 5, 20:00:00 hora de Lima, pasos de kg.

Ver `docs/sdd/02-especificacion-cun-02.md`.

## ¿Cómo controlaron la ambigüedad?

Con un documento de clarificación **antes** del código (`docs/sdd/10-clarificaciones-v2.md`): 12 decisiones con autor y fecha, y 12 supuestos con valor concreto.

Ejemplos de ambigüedades cerradas:
- ¿las 20:00:00 están dentro o fuera? → fuera;
- ¿el mínimo se compara redondeado? → no;
- ¿qué pasa si falla una zona? → reembolso del 100 %.

## ¿Cómo verificaron que el software cumple la especificación?

Cada criterio tiene una prueba con el mismo identificador (`test_ca04_*`, `test_cl08_*`). Las pruebas verifican el **código de error** del contrato, no el mensaje.

- 45 pruebas en verde.
- Evidencia en rojo antes del código.
- Demo por consola.
- Matriz `docs/sdd/06-trazabilidad.md`.

## ¿Qué ocurre cuando cambia una especificación?

Nos pasó tres veces, y en Git se ve el orden `docs → test → feat`:

1. **RN-21 → precio máximo.** Al revisar el modelo encontramos que cobrar un saldo en la puerta viola la Ley 29571. Se reescribió la regla (C-01), luego la spec, los criterios, las pruebas y el código.
2. **Cotización.** Al escribir las pruebas vimos que el cliente necesita saber cuánto yapear. Entró primero como `docs:`.
3. **Faltante en un pedido no entregado.** Salió al diseñar la liquidación. Entró como `docs:`, luego `test:` y después `feat:`.

## ¿Cómo relacionaron las reglas con el código?

Cada función indica la regla que implementa (por ejemplo, `# RP-10: se compara el valor exacto` en `order_registration.py:116`). La matriz de trazabilidad da la línea exacta. El recorrido completo de una spec está al final de `docs/sdd/06-trazabilidad.md`.

## ¿Qué impacto tuvo SDD en el diseño?

- Las reglas no dependen de la consola ni del almacenamiento. Por eso se separaron `domain`, `cycle`, `store`, `order_registration`, `settlement` y `cli`.
- La spec obligó a que el precio y la zona salgan del sistema y no del cliente. Eso cambió la firma de `register_order`: no recibe precio.
- La propiedad "nunca se paga de más" se convirtió en un invariante con su prueba (CL-08).

## ¿Por qué no implementaron todo Yapa?

Porque el lab pide demostrar la metodología sobre funcionalidades con lógica de negocio. El resto está declarado fuera de alcance, con su motivo, y en el roadmap del repositorio general.

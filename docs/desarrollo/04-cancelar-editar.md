# Iteración 4 · Cancelar y editar el pedido antes del cierre

## Requisito

Como vecino, quiero poder cancelar o cambiar mi pedido mientras el ciclo sigue abierto y recuperar mi dinero, porque todavía no se compró nada con él.

Como Yapa, quiero que después del cierre ya no haya cambios, porque con esos pedidos se calculan los descuentos de todos y se hace la compra.

## Decisión del equipo que se aplica

Carlos (24/09/2026): *"la devolución ya no se puede si el personal ya compró los artículos (afecta al cálculo de los vecinos y a nosotros), pero si todavía no se compró tiene la opción de que se le devuelva"*.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-18 | El **corte para cancelar o editar es el cierre del miércoles a las 20:00**, no la hora de compra. Al cierre se calculan los tramos, así que un cambio posterior afectaría a los vecinos. | Igual que RP-03 |
| S-19 | Al cancelar, el cliente **elige** si la parte pagada por Yape/Plin vuelve a su medio de pago (reembolso pendiente, 30 días) o a su saldo. La parte pagada con saldo siempre vuelve al saldo. | Por defecto, al medio de pago |
| S-20 | Si el pago externo **todavía no fue verificado**, se cancela sin reembolso automático de esa parte (igual que LQ-01). Atención al cliente resuelve si el pago sí llegó. | — |
| S-21 | Un código de operación usado no se libera al cancelar: no se puede reutilizar. | — |
| S-22 | Si al editar el total **baja**, la diferencia vuelve como **saldo** (el cliente puede pedirla de vuelta con BS-12). Así no se hacen devoluciones por Yape en cada cambio. | — |
| S-24 | Al bajar un pedido, **solo se devuelve a saldo dinero ya confirmado**. Primero se reduce el pago externo **sin verificar** (el cliente simplemente debe menos), después el pago con saldo y al final el pago externo verificado. Solo lo reducido de estos dos últimos vuelve al saldo. *(Detectado al diseñar la edición: sin esto, alguien podría registrar con un código falso, bajar el pedido y cobrar la diferencia como saldo.)* | — |
| S-23 | Si al editar el total **sube**, el cliente paga la diferencia (saldo y/o Yape/Plin con un código nuevo). Ese pago queda `POR_VERIFICAR` y aplica LQ-01: si no se verifica antes del cierre, el pedido completo se cancela. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| CE-01 | Solo el dueño puede cancelar o editar su pedido. Para cualquier otro cliente, el pedido "no existe". | `ORDER_NOT_FOUND` |
| CE-02 | Solo se cancela o edita un pedido `REGISTRADO`. | `ORDER_NOT_EDITABLE` |
| CE-03 | Solo antes del cierre del ciclo del pedido (S-18). | `CYCLE_CLOSED` |
| CE-04 | Al cancelar, el pedido pasa a `CANCELADO_POR_CLIENTE` y se libera su stock reservado. | — |
| CE-05 | Devolución al cancelar: saldo usado → saldo; pago externo verificado → destino elegido (S-19); pago externo sin verificar → sin reembolso automático (S-20). | `INVALID_REFUND_DESTINATION` |
| CE-06 | RP-04 pasa a ser **un pedido activo** por ciclo: tras cancelar, el cliente puede registrar otro. | — |
| CE-07 | La liquidación ignora los pedidos cancelados por el cliente: no cuentan para el mínimo, los tramos ni el envío. | — |
| CE-08 | Editar reemplaza las líneas del pedido con las mismas reglas RP-05..RP-11. Para el stock, lo que el propio pedido ya tenía reservado cuenta como disponible. | los de RP-05..RP-10 |
| CE-09 | Si el nuevo total baja, la diferencia va a saldo (S-22) y los pagos se ajustan para que siempre sumen el total del pedido (primero se reduce el pago con saldo, luego el externo). | — |
| CE-12 | Al bajar el total, el orden de reducción y lo que vuelve al saldo siguen S-24. | — |
| CE-10 | Si el nuevo total sube, se exige el pago de la diferencia exacta (BS-03..BS-06 aplicados a la diferencia) (S-23). | `PAYMENT_AMOUNT_MISMATCH`, etc. |
| CE-11 | Si la edición falla por cualquier regla, el pedido queda exactamente como estaba. | — |

## Criterios de aceptación

Pedido base: 5 kg de papa amarilla + 4 galones de limpiatodo = subtotal S/ 54.604, total **S/ 59.60**, pagado por Yape y verificado.

- **CC-01 · Cancelar con devolución al medio de pago.** ENTONCES el pedido queda `CANCELADO_POR_CLIENTE`, hay un reembolso pendiente de S/ 59.60 y el stock reservado de papa vuelve a 0. → CE-04, CE-05
- **CC-02 · Cancelar con devolución a saldo.** ENTONCES el saldo del vecino es S/ 59.60 y no hay reembolso pendiente. → CE-05
- **CC-03 · Cancelar un pedido pagado con saldo + Yape.** Con S/ 10 de saldo y S/ 49.60 de Yape, eligiendo medio de pago: vuelven S/ 10 al saldo y queda un reembolso pendiente de S/ 49.60. → CE-05
- **CC-04 · Cancelar sin pago verificado.** ENTONCES se cancela y no hay reembolso pendiente (S-20). → CE-05
- **CC-05 · Después del cierre.** Cancelar el miércoles a las 20:00 → `CYCLE_CLOSED`. → CE-03
- **CC-06 · Pedido ajeno.** Otro cliente intenta cancelarlo → `ORDER_NOT_FOUND`. → CE-01
- **CC-07 · Cancelar dos veces.** → `ORDER_NOT_EDITABLE`. → CE-02
- **CC-08 · Nuevo pedido tras cancelar.** El mismo vecino registra otro pedido en el ciclo → se acepta. El código de operación anterior no se puede reutilizar. → CE-06, S-21
- **CC-09 · Destino inválido.** Elegir destino `TARJETA` → `INVALID_REFUND_DESTINATION`. → CE-05
- **CC-10 · La liquidación ignora cancelados.** Grupo con 8 pedidos, de los cuales 1 se cancela: quedan 7, el grupo no se atiende, y el cancelado no aparece como `NO_ATENDIDO` ni recibe un segundo reembolso. → CE-07
- **CE-A · Editar a menos.** Cambiar a 6 kg de papa + 3 galones → total S/ 55.02. Vuelven S/ 4.58 a saldo, los pagos suman S/ 55.02 y la reserva de limpiatodo baja a 3. → CE-08, CE-09
- **CE-B · Editar a más.** Cambiar a 5 kg + 5 galones → total S/ 68.21. Se paga la diferencia de S/ 8.61 con un código nuevo, y el pedido queda `POR_VERIFICAR`. → CE-10
- **CE-C · Diferencia mal pagada.** Pagar S/ 8.00 en vez de S/ 8.61 → `PAYMENT_AMOUNT_MISMATCH` y el pedido no cambia. → CE-10, CE-11
- **CE-D · Editar bajo el mínimo.** Dejar solo 5 galones (S/ 43.055) → `SUBTOTAL_BELOW_MINIMUM` y el pedido no cambia. → CE-08, CE-11
- **CE-E · Stock propio.** Con 395 kg reservados por otros y 5 kg por este pedido (máximo 400): editar manteniendo 5 kg se acepta; subir a 6 kg → `PRODUCT_SOLD_OUT`. → CE-08
- **CE-F · Editar después del cierre.** → `CYCLE_CLOSED`. → CE-03
- **CE-H · No se regala saldo sin pago confirmado.** DADO el pedido base con el Yape **sin verificar**, CUANDO se edita a S/ 55.02, ENTONCES el saldo del vecino sigue en S/ 0 y el pago pendiente baja a S/ 55.02. → CE-12
- **CE-G · Zona no atendida tras bajar el pedido.** El pedido editado a S/ 55.02 (S/ 4.58 ya en saldo) no se atiende: se reembolsan S/ 55.02 al medio de pago, y en total el vecino recupera S/ 59.60. → CE-09, BS-09

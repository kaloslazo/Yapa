# Iteración 3 · Billetera de saldo

## Requisito

Como vecino, quiero que lo que Yapa me devuelve quede guardado como saldo, poder usarlo en mi próxima compra (solo o junto con Yape/Plin) y, si ya no quiero comprar, pedir que me lo devuelvan a mi medio de pago.

Como Yapa, quiero saber en todo momento cuánto le debo a cada cliente, porque el saldo es plata de ellos.

## Decisiones que se aplican

- **C-05**: el saldo **no vence**, y el cliente puede pedir la devolución a su medio de pago (hasta 30 días).
- **C-06**: si la zona no llega al mínimo, se devuelve al medio de pago, **no** a saldo.
- **Iteración 2 (LQ-08)**: la diferencia de la liquidación va a `SALDO`.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-13 | Un pedido puede pagarse con **varios pagos**: saldo + Yape/Plin. | Máximo un pago de saldo y un pago externo al registrar. |
| S-14 | Si el saldo cubre todo el total, no se pide código de operación y ese pago queda `VERIFICADO` al instante. | — |
| S-15 | Las devoluciones de dinero, ya sea por zona no atendida o a pedido del cliente, se registran como **reembolsos pendientes** con fecha límite. El administrador las marca como pagadas con su código de operación. | Plazo: 30 días desde la solicitud. |
| S-16 | Si un pedido pagado en parte con saldo no se atiende o queda cancelado, **la parte de saldo vuelve al saldo** y la parte externa sigue la regla de siempre. | — |
| S-17 | Un ciclo se liquida **una sola vez**. Así el saldo no se abona dos veces. | — |

## Reglas

### Billetera

| Regla | Comportamiento | Error |
|---|---|---|
| BS-01 | El saldo del cliente es la suma de sus movimientos: abonos (liquidación, devolución de saldo usado) menos cargos (uso en pedido, devolución solicitada). Nunca es negativo. | — |
| BS-02 | El saldo no vence: un abono de hace un año se puede usar igual. | — |

### Registrar pedido con saldo (extiende RP-12..RP-14)

| Regla | Comportamiento | Error |
|---|---|---|
| BS-03 | El saldo a usar debe ser ≥ 0 y no mayor que el saldo disponible. | `INSUFFICIENT_BALANCE` |
| BS-04 | El saldo a usar no puede ser mayor que el total del pedido. | `BALANCE_EXCEEDS_TOTAL` |
| BS-05 | El monto pagado por Yape/Plin debe ser exactamente total − saldo usado. | `PAYMENT_AMOUNT_MISMATCH` |
| BS-06 | Si el saldo cubre todo el total, no se exige medio ni código de operación (S-14). Si no lo cubre, se aplican RP-12 y RP-13 al pago externo. | — |
| BS-07 | Al registrar, el saldo usado se descuenta de la billetera (movimiento `USO_EN_PEDIDO`). | — |

### Liquidación (extiende LQ-01, LQ-02 y LQ-08)

| Regla | Comportamiento | Error |
|---|---|---|
| BS-08 | Pedido `LIQUIDADO`: el saldo a favor se abona a la billetera (`ABONO_LIQUIDACION`). | — |
| BS-09 | Pedido `NO_ATENDIDO`: la parte externa se registra como reembolso pendiente al medio de pago y la parte de saldo vuelve a la billetera (S-16). | — |
| BS-10 | Pedido `CANCELADO` (sin pago verificado): la parte de saldo vuelve a la billetera. La parte externa no tiene reembolso automático (LQ-01). | — |
| BS-11 | Un ciclo ya liquidado no se puede volver a liquidar (S-17). | `CYCLE_ALREADY_SETTLED` |

### Devolución del saldo a pedido del cliente

| Regla | Comportamiento | Error |
|---|---|---|
| BS-12 | El cliente puede pedir que le devuelvan un monto de su saldo (> 0 y ≤ saldo). El monto se descuenta en el momento y queda un reembolso pendiente con fecha límite de 30 días. | `INVALID_AMOUNT`, `INSUFFICIENT_BALANCE` |
| BS-13 | El administrador marca un reembolso pendiente como pagado con su código de operación. No se puede pagar dos veces. | `REFUND_NOT_FOUND`, `REFUND_ALREADY_PAID` |
| BS-14 | Se puede consultar el total que Yapa le debe a sus clientes: saldos más reembolsos pendientes. | — |

## Criterios de aceptación

- **CB-01 · Liquidación abona saldo.** DADO un ciclo liquidado donde a un vecino le vuelven S/ 12.86, ENTONCES su saldo es S/ 12.86. → BS-01, BS-08
- **CB-02 · Usar saldo parcial.** DADO un vecino con S/ 12.86 de saldo y un pedido de S/ 59.51, CUANDO usa todo su saldo y yapea S/ 46.65, ENTONCES el pedido se registra con dos pagos y su saldo queda en S/ 0. → BS-03, BS-05, BS-07
- **CB-03 · Saldo cubre todo.** DADO un vecino con S/ 70 de saldo, CUANDO paga el pedido de S/ 59.51 solo con saldo y sin código de operación, ENTONCES el pedido queda con pago `VERIFICADO` y le quedan S/ 10.49. → BS-06
- **CB-04 · Saldo insuficiente.** DADO un vecino con S/ 5 de saldo, CUANDO intenta usar S/ 10, ENTONCES se rechaza con `INSUFFICIENT_BALANCE`. → BS-03
- **CB-05 · Saldo mayor al total.** DADO un vecino con S/ 100, CUANDO intenta usar S/ 60 en un pedido de S/ 59.51, ENTONCES se rechaza con `BALANCE_EXCEEDS_TOTAL`. → BS-04
- **CB-06 · Monto externo incorrecto.** DADO S/ 12.86 de saldo usado en un pedido de S/ 59.51, CUANDO yapea S/ 59.51, ENTONCES se rechaza con `PAYMENT_AMOUNT_MISMATCH`. → BS-05
- **CB-07 · Saldo no vence.** DADO un abono hecho hace 400 días, ENTONCES el saldo se puede usar igual. → BS-02
- **CB-08 · Zona no atendida con saldo.** DADO un pedido de S/ 61.00 pagado con S/ 10 de saldo y S/ 51 por Yape en un grupo que no llega al mínimo, ENTONCES se registra un reembolso pendiente de S/ 51 al medio de pago y los S/ 10 vuelven al saldo. → BS-09
- **CB-09 · Cancelado con saldo.** DADO un pedido pagado en parte con saldo que no verificó su pago externo, ENTONCES la parte de saldo vuelve a la billetera. → BS-10
- **CB-10 · Liquidar dos veces.** DADO un ciclo ya liquidado, CUANDO se intenta liquidar otra vez, ENTONCES se rechaza con `CYCLE_ALREADY_SETTLED` y el saldo no cambia. → BS-11
- **CB-11 · Pedir devolución.** DADO S/ 12.86 de saldo, CUANDO el vecino pide S/ 10 de vuelta el 20/09/2026, ENTONCES su saldo queda en S/ 2.86 y existe un reembolso pendiente de S/ 10 con fecha límite 20/10/2026. → BS-12
- **CB-12 · Devolución inválida.** Pedir S/ 0 → `INVALID_AMOUNT`. Pedir más que el saldo → `INSUFFICIENT_BALANCE`. → BS-12
- **CB-13 · Pagar un reembolso.** DADO un reembolso pendiente, CUANDO el administrador lo marca pagado con un código, ENTONCES queda `PAGADO`. Pagarlo de nuevo → `REFUND_ALREADY_PAID`. Uno inexistente → `REFUND_NOT_FOUND`. → BS-13
- **CB-14 · Deuda con clientes.** DADO saldos de S/ 12.86 y S/ 2.86 y un reembolso pendiente de S/ 10, ENTONCES Yapa le debe S/ 25.72 a sus clientes. → BS-14

## Impacto en el diseño

- `Order` pasa de un solo pago a una **lista de pagos** (`Payment`: medio, monto, código, estado). Para no romper el contrato de la iteración 2, `payment_status` y `payment_method` se mantienen como propiedades derivadas.
- Nuevo módulo `wallet.py`, con la billetera, los movimientos y los reembolsos pendientes.
- `settlement.py` abona a la billetera y registra reembolsos. Guarda qué ciclos ya se liquidaron.

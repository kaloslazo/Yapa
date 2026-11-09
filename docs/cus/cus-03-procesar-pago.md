# Yapa — CUS-03 Procesar pago y saldo

**Fuente de las reglas:** `api/docs/sdd/02-especificacion-cun-02.md` (RP-12..RP-15), `api/docs/desarrollo/03-billetera-saldo.md` (BS), `19-conciliacion-punta-a-punta.md` (AU) y `26-experiencia-compra.md` (S-148, S-150). Decisiones C-03, C-04 y C-05.

## 0. Objetivo y frontera

Confirmar que el dinero de cada pedido llegó, mantener el saldo a favor de cada vecino y devolverle su dinero cuando lo pide, sin que las cuentas de Yapa dejen de cuadrar.

Yapa cobra en una cuenta **Plin negocios**, que no cobra comisión (decisión del 09/11/2026, iteración 58). El vecino puede pagar desde Plin o desde Yape, porque las dos billeteras funcionan entre sí desde 2023. Yape y Plin no tienen API pública: el vecino paga fuera del sistema al número que le muestra la confirmación, con el código `YP-…` en el mensaje (CUS-02), y el **administrador** verifica el pago comparando con su app. Actores: **administrador** (verifica y concilia), **atención** (paga devoluciones) y **vecino** (pide devoluciones).

## 1. Requerimientos funcionales

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-03.1 | El administrador ve los pedidos `POR_VERIFICAR` del ciclo con su código de pago y monto, y los verifica antes del cierre. | RP-15, S-150 | Verificar un pedido inexistente → `ORDER_NOT_FOUND`; después del cierre → `CYCLE_CLOSED`. |
| RF-03.2 | Un pedido que sigue `POR_VERIFICAR` al cierre queda `CANCELADO` y no se compra. | LQ-01 | La parte pagada con saldo vuelve a la billetera (BS-10). |
| RF-03.3 | El saldo es la suma de sus movimientos, nunca negativo y no vence. | BS-01, BS-02, C-05 | Un abono de hace 400 días se puede usar. |
| RF-03.4 | El vecino pide devolver parte o todo su saldo a su Yape o Plin; se descuenta al instante y queda un reembolso pendiente con plazo de 30 días. | BS-12 | Monto 0 → `INVALID_AMOUNT`; más que el saldo → `INSUFFICIENT_BALANCE`. |
| RF-03.5 | El administrador o atención marcan el reembolso como pagado con su código de operación, una sola vez. | BS-13, AT-02 | Pagar dos veces → `REFUND_ALREADY_PAID`. |
| RF-03.7 | La confirmación del pedido dice a qué Plin pagar (número y titular) mientras el pago está por verificar. | PL-01, S-305 | Proyecto académico: sin cuenta configurada se muestra una cuenta simulada, marcada como tal. |
| RF-03.6 | El sistema concilia: recibido = en curso + retenido + deuda con clientes + devoluciones pagadas, con diferencia 0. | AU-01..AU-04 | `/admin/conciliacion` muestra "Cuadra" con diferencia S/ 0,00. |

## 2. Ficha

| Campo | Descripción |
|---|---|
| Identificador | CUS-03 |
| Actores | Administrador (principal), atención, vecino |
| Disparador | Llega un Yape o Plin con un código `YP-…`, o el vecino pide su saldo de vuelta. |
| Precondiciones | Pedido registrado (CUS-02) o vecino con saldo. |
| Postcondición de éxito | Pago `VERIFICADO` en el registro de caja; o reembolso `PAGADO`. La conciliación sigue en 0. |
| Garantía ante fallo | Un pago no se registra dos veces en la caja; un reembolso no se paga dos veces. |

## 3. Flujo principal (verificar un pago)

| Paso | Administrador | Sistema |
|---|---|---|
| 1 | Abre "Pagos por verificar". | Lista los pedidos `POR_VERIFICAR` del ciclo con vecino, monto y código `YP-…`. |
| 2 | Busca el código en su app de Yape o Plin y confirma. | Pide confirmar la acción. |
| 3 | Confirma. | Verifica que el ciclo siga abierto, marca el pago `VERIFICADO` y lo suma al registro de caja una sola vez (AU-01). |

### Subflujo: devolver saldo

| Paso | Actor | Sistema |
|---|---|---|
| 1 | El vecino, en Mi cuenta, pide devolver S/ X a su Yape o Plin. | Valida el monto, descuenta el saldo y crea un reembolso pendiente con fecha límite (+30 días). |
| 2 | Atención o el administrador transfieren y registran el código de operación. | Marca el reembolso `PAGADO`. |

## 4. Flujos alternativos y excepciones

| Código | Condición | Respuesta |
|---|---|---|
| FA-01 | El saldo cubre todo el pedido. | No hay pago externo; el pedido nace `VERIFICADO` (BS-06). |
| FA-02 | El pago no llega antes del cierre. | El pedido queda `CANCELADO`; el saldo usado vuelve a la billetera. |
| FA-03 | La zona no llega al mínimo. | Reembolso pendiente del 100 % de lo pagado al medio de pago y el saldo usado vuelve (C-06, BS-09). Ver CUS-04. |
| EX-01 | Verificar después del cierre. | `CYCLE_CLOSED`. |
| EX-02 | Devolución inválida. | `INVALID_AMOUNT` o `INSUFFICIENT_BALANCE`. |
| EX-03 | La conciliación no da 0. | La pantalla lo marca en rojo con la diferencia. |

## 5. Escenarios de aceptación

1. **Saldo parcial.** Con S/ 12,86 de saldo y un pedido de S/ 59,51, el vecino usa todo su saldo y yapea S/ 46,65 → dos pagos, saldo en 0. (CB-02)
2. **Saldo cubre todo.** Con S/ 70 de saldo paga los S/ 59,51 → pago `VERIFICADO`, quedan S/ 10,49. (CB-03)
3. **Pedir devolución.** Con S/ 12,86 pide S/ 10 el 20/09 → saldo S/ 2,86 y reembolso pendiente hasta el 20/10. (CB-11)
4. **Deuda con clientes.** Saldos de S/ 12,86 y S/ 2,86 más un reembolso pendiente de S/ 10 → Yapa debe S/ 25,72. (CB-14)
5. **Conciliación.** Un pedido de S/ 61,00 verificado → recibido 61,00, en curso 61,00, diferencia 0; después de liquidar 8 pedidos → recibido 488,00 = retenido + saldos. (AU-A)

## 6. Pantallas y código

- Web: panel → Pagos, Devoluciones y Conciliación; Mi cuenta → Devolver saldo.
- API: `/api/admin/pedidos/{id}/verificar`, `/api/saldo/devolucion`, `/api/admin/devoluciones/*`, `/api/admin/conciliacion`.
- Motor: `order_registration.verify_payment`, `wallet.py`, `audit.money_balance`.
- Prueba de punta a punta: `api/tests/test_e2e_week.py` (la diferencia es 0 después de cada paso).

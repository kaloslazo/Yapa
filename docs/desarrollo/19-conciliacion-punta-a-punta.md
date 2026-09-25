# Iteración 19 · Conciliación del dinero y semana completa de punta a punta

## Requisito

Como Yapa, quiero comprobar en cualquier momento que **ningún sol se crea ni se pierde**: todo lo que los vecinos pagaron está en lo que Yapa se quedó, en lo que les debe o en lo que ya les devolvió. Como el saldo es plata de los clientes (C-05), esto es lo mínimo para operar con confianza.

Además, quiero una prueba que recorra **una semana completa por la web**, como la usaría el equipo, para verificar que todas las iteraciones funcionan juntas.

## Por qué

Hasta la iteración 18, cada regla se probó por separado. Ninguna prueba verificaba que el dinero cuadre después de muchas operaciones combinadas: pedidos, pagos con saldo, cancelaciones, ediciones, zonas no atendidas, reclamos y devoluciones.

Al diseñar esta iteración apareció un hueco: **cuando se edita un pedido a la baja, el pago se reduce y se pierde el registro de cuánto se había recibido de verdad**. La conciliación necesita saber lo recibido, así que se agrega un registro de caja.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-113 | Un pago por Yape/Plin cuenta como **dinero recibido** cuando el administrador lo verifica. Lo pagado con saldo no es dinero nuevo: es plata que Yapa ya debía. | — |
| S-114 | Se lleva un **registro de caja** con cada pago externo verificado (pedido, medio, monto, código, fecha). Ese registro no cambia aunque después el pedido se edite o se cancele. | — |
| S-115 | Conciliación: **recibido = en curso + retenido por Yapa + deuda con clientes + devoluciones ya pagadas**. | — |
|  | - **En curso:** pagos verificados (incluido el saldo usado) de pedidos todavía `REGISTRADO`, es decir, plata que Yapa tiene por pedidos sin liquidar. *(Se agregó al diseñar: sin esto, la conciliación daría una diferencia falsa entre el pago y la liquidación.)* | |
|  | - **Retenido:** Σ montos finales de pedidos liquidados o no entregados − Σ reclamos aprobados. | |
|  | - **Deuda:** saldos + devoluciones pendientes (BS-14). | |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AU-01 | Al verificar un pago externo se agrega al registro de caja (S-114). Verificar dos veces no lo agrega dos veces. | — |
| AU-02 | `money_balance` devuelve: recibido, en curso, retenido, deuda con clientes, devoluciones pagadas y la **diferencia**, que debe ser 0 (S-115). | — |
| AU-03 | El administrador ve la conciliación en la web (`/admin/conciliacion`), con un aviso claro si la diferencia no es 0. | — |
| AU-04 | La conciliación da 0 después de **cada** paso de una semana completa hecha por la web. | — |

## Criterios de aceptación

- **AU-A · Pedido simple.** Un pedido de S/ 61.00 verificado: recibido 61.00, **en curso 61.00**, retenido 0, deuda 0 → diferencia 0. Después de liquidar (8 pedidos): recibido 488.00 = retenido + saldos → diferencia 0. → AU-01, AU-02
- **AU-B · Edición a la baja.** Un pedido de S/ 59.60 verificado que se edita a S/ 55.02: recibido sigue en 59.60 (registro de caja) y la deuda es de 4.58 (saldo) → diferencia 0. → S-114
- **AU-C · Semana completa por la web** (AU-04). Se hace todo por HTTP y la diferencia es 0 después de cada paso:
  1. Miércoles: 9 vecinos de Jesús María piden y el admin verifica sus pagos; uno cancela a saldo. Además, 2 vecinos de Lince piden (su grupo no llega al mínimo).
  2. Sábado: el admin arma los 8 pedidos de Jesús María y entrega la zona.
  3. El admin liquida (`close_cycle`): Jesús María queda `LIQUIDADO` y Lince `NO_ATENDIDO`.
  4. Un vecino reclama 1 kg de cebolla faltante y el admin lo aprueba.
  5. Ese vecino pide la devolución de S/ 10 de su saldo y el admin la paga con código.
  6. El admin ve las métricas y la conciliación con diferencia 0.
- **AU-D · Pantalla.** `/admin/conciliacion` muestra "Cuadra" con diferencia S/ 0.00. → AU-03

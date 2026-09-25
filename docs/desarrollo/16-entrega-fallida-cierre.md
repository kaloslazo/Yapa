# Iteración 16 · Entrega fallida y cierre del ciclo

## Requisito

Como Yapa, si el sábado la portería de una zona no recibe (está cerrada, no hay nadie o se niega), quiero **registrarlo con evidencia** y que los vecinos de esa zona recuperen su plata de forma justa.

Además, quiero que el ciclo **solo se liquide cuando todas las zonas atendidas se entregaron o se registró su falla**, para no liquidar a ciegas.

## Origen

- **Decisión urgente n.º 3** de `supuestos-a-validar.md` y hueco H1.11 (`docs/analisis/03_huecos_negocio.md`).
- **Hueco 2 de la iteración 7:** `settle_cycle` no exige que la zona esté entregada.
- **Recomendación del cuestionario del 23/09 (D-22):** reembolso menos el delivery y sin reintento en el piloto. Carlos pidió usar las recomendaciones como supuestos a validar.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-102 | **Sin reintento en el piloto:** si la zona no recibe, esa entrega queda como fallida para el ciclo. | — |
| S-103 | Los vecinos de una zona con entrega fallida recuperan **todo lo pagado menos el envío real de la zona**, porque el camión sí fue. Se devuelve como **saldo**, que pueden pedir a su Yape/Plin (BS-12). | — |
| S-104 | Lo comprado para una zona fallida **cuenta igual para los tramos por volumen**, porque ya se compró. Los frescos se pierden (merma que asume Yapa). La limpieza puede pasar al colchón a mano, con el tope de S-46. | — |
| S-105 | El motivo de la falla es uno de: `PORTERIA_CERRADA`, `NADIE_RECIBE`, `PORTERIA_RECHAZA`. | — |
| S-106 | **Cerrar el ciclo** es la operación del día a día: exige que cada zona atendida esté entregada o fallida y recién entonces liquida. `settle_cycle` sigue siendo el cálculo puro que usan las pruebas y el simulador. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| EF-01 | Registrar entrega fallida: solo el personal (S-40), con una zona que existe, con foto de evidencia y motivo válido (S-105). | `NOT_AUTHORIZED`, `ZONE_NOT_FOUND`, `PHOTO_REQUIRED`, `INVALID_FAILURE_REASON` |
| EF-02 | La zona tiene pedidos atendidos y todos armados: el camión llevó las bolsas (igual que EN-04 y EN-05). | `NOTHING_TO_DELIVER`, `ORDERS_NOT_PACKED` |
| EF-03 | Una zona se entrega **o** falla una sola vez por ciclo (S-102). | `ZONE_ALREADY_CLOSED` |
| EF-04 | En la liquidación, los pedidos atendidos de una zona fallida quedan `NO_ENTREGADO`: se cobra solo el envío real de la zona y el resto vuelve como saldo (S-103). Sus cantidades cuentan para los tramos (S-104). | — |
| EF-05 | No se puede reclamar un pedido de una zona fallida: ya recibió todo como saldo. | `ORDER_NOT_DELIVERED` (regla existente) |
| EF-06 | `close_cycle` liquida solo si cada zona con pedidos atendidos está entregada o fallida. Si no, informa qué zonas faltan. | `ZONES_PENDING` |

## Criterios de aceptación

Escenario: 8 pedidos en Jesús María (canasta de S/ 61.00), armados.

- **EF-A · Registrar falla.** El personal registra `PORTERIA_CERRADA` con foto → queda registrada. Después, entregar o volver a fallar la misma zona → `ZONE_ALREADY_CLOSED`. → EF-01, EF-03
- **EF-B · Plata de vuelta.** Al liquidar, los 8 pedidos quedan `NO_ENTREGADO`. El monto final de cada uno es el envío real (40 ÷ 8 = **S/ 5.00**) y vuelven **S/ 56.00** a su saldo. La papa amarilla sigue contando 40 kg para los tramos. → EF-04
- **EF-C · Datos obligatorios.** Sin motivo o con motivo `LLUVIA` → `INVALID_FAILURE_REASON`. Sin foto → `PHOTO_REQUIRED`. Si no es personal → `NOT_AUTHORIZED`. Con pedidos sin armar → `ORDERS_NOT_PACKED`. → EF-01, EF-02
- **EF-D · Sin reclamos.** Un vecino de la zona fallida intenta reclamar → `ORDER_NOT_DELIVERED`. → EF-05
- **EF-E · Cierre con zonas pendientes.** Con Jesús María entregada y un grupo de Lince atendido sin entregar ni fallar → `close_cycle` da `ZONES_PENDING` y nombra la zona de Lince. Nadie recibe saldo todavía. → EF-06
- **EF-F · Cierre completo.** Con todas las zonas entregadas o fallidas → `close_cycle` liquida y devuelve lo mismo que `settle_cycle`. → EF-06

## Huecos que siguen abiertos

- En las métricas (S-47), los pedidos `NO_ENTREGADO` no cuentan como compra, y **la merma de los frescos de una zona fallida todavía no aparece como pérdida en el margen**. Queda para una próxima iteración de métricas.

## Trazabilidad

| Regla | Código | Prueba (`tests/test_failed_delivery.py`) |
|---|---|---|
| EF-01..EF-03, S-102, S-105 | `fulfillment.register_failed_delivery`, `_ready_orders`; `deliver_zone` rechaza una zona fallida | `test_ef_a_*`, `test_ef_c_*` |
| EF-04, S-103, S-104 | `settlement.settle_cycle` (zona fallida → todo "faltante", se cobra solo el envío real, abono `DEVOLUCION_NO_ENTREGADO`) | `test_ef_b_*` |
| EF-05 | `claims.file_claim` (regla existente: sin entrega no hay reclamo) | `test_ef_d_*` |
| EF-06, S-106 | `fulfillment.close_cycle` | `test_ef_e_*`, `test_ef_f_*` |

# Iteración 17 · La pérdida de una zona fallida aparece en el margen

## Requisito

Como equipo, si una portería no recibe, queremos **ver cuánto perdimos** en las métricas. Si no, el tablero de margen dice que todo está bien justo cuando más se perdió.

## Origen

Hueco abierto de la iteración 16: los pedidos `NO_ENTREGADO` no entraban en `order_margins` (S-47 solo contaba `LIQUIDADO`), así que la merma no se veía.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-107 | En el **margen**, un pedido `NO_ENTREGADO` cuenta con: ingreso = el envío real que se le cobró, costo del proveedor = precio del tramo × cantidad **pedida** (se compró igual), y su parte de la parada. Se asume pérdida total de lo comprado, aunque la limpieza pueda ir luego al colchón (criterio conservador). | — |
| S-108 | Para la **recompra** y el **ahorro entregado**, un pedido `NO_ENTREGADO` sigue sin contar (S-47 y S-51 no cambian). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| MG-01 | `order_margins` incluye los pedidos `NO_ENTREGADO` según S-107. | — |
| MG-02 | `margin_alerts` y el margen neto (iteración 13) los incluyen, porque se calculan sobre `order_margins`. | — |
| MG-03 | La recompra y el ahorro entregado no cambian (S-108). | — |

## Criterios de aceptación

Escenario EF-B: 8 pedidos en Jesús María, zona fallida.

- **MG-A · Pérdida visible.** Cada pedido: ingreso S/ 5.00, costo del proveedor **S/ 47.00** (lo mismo que en MT-A, porque se compró igual), parada S/ 5.00 → margen **−S/ 47.00**. Los 8 aparecen en las alertas. → MG-01, MG-02
- **MG-B · Métricas sin fallas no cambian.** En el escenario MT-A (sin fallas), el margen sigue siendo S/ 5.64. → MG-01
- **MG-C · Ahorro y recompra sin cambio.** En la zona fallida, el ahorro entregado del ciclo es S/ 0 (nadie recibió). → MG-03

## Trazabilidad

| Regla | Código (`src/yapa_sdd/metrics.py`) | Prueba (`tests/test_failed_zone_metrics.py`) |
|---|---|---|
| MG-01, S-107 | `order_margins` (incluye `NO_ENTREGADO`, costo sobre lo pedido) | `test_mg_a_*`, `test_mg_b_*` |
| MG-02 | `margin_alerts` y `net_margins` usan `order_margins` | `test_mg_a_*` |
| MG-03, S-108 | `delivered_savings` y `repurchase_week4` siguen usando `_liquidated` | `test_mg_c_*` |

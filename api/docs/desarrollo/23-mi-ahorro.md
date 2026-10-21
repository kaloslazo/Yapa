# Iteración 23 · "Te devolvemos" y el ahorro en Mi cuenta

## Requisito

Como vecino, quiero ver en "Mi cuenta" cuánto costó de verdad mi pedido, cuánto me devolvieron y cuánto habría pagado en el mercado, para confiar en Yapa y volver a pedir.

## Por qué

- La promesa del modelo es "pagas el máximo y **te devolvemos** lo que ahorremos" (C-05). Hoy "Mi cuenta" solo muestra el total pagado y el saldo. El vecino no ve **de dónde** salió su saldo.
- La recompra en la semana 4 es la métrica que decide si el piloto sigue (iteración 8, meta de 50 %). Mostrar el ahorro es la forma más directa de ayudarla.
- La iteración 22 ya calcula la comparación por canasta. Esta iteración la muestra por pedido.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-130 | En cada pedido liquidado, "Mi cuenta" muestra lo que pagó, lo que costó al final y lo que se le devolvió, y a dónde fue (saldo o Yape/Plin). En un pedido no atendido o no entregado, muestra lo devuelto. | — |
| S-131 | Si la canasta del pedido es comparable (S-129), se muestra cuánto costaba en el mercado de barrio y en el supermercado, y la diferencia. Si Yapa salió más caro, también se dice ("pagaste S/ X más"), igual que en S-127. | — |
| S-132 | Arriba de la cuenta se muestra el total devuelto en todos sus pedidos: "Con Yapa ya te devolvimos S/ X". | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| MA-01 | `order_comparison(store, pedido)` da, por tipo de referencia, el costo de la canasta allá y la diferencia con el monto final, solo si el pedido está liquidado y es comparable (S-129). | — |
| MA-02 | "Mi cuenta" muestra el detalle de S-130 y S-131 en cada pedido del vecino. | — |
| MA-03 | "Mi cuenta" muestra el total devuelto de S-132 (suma de lo devuelto en sus pedidos liquidados, no atendidos o no entregados). | — |
| MA-04 | La iteración 22 usa la misma cuenta por canasta: `reference_savings` no cambia sus números. | — |

## Criterios de aceptación

Escenario de la iteración 22: 8 pedidos en Jesús María con la canasta de prueba (S/ 61.00 cada uno), precios de referencia del 17/09, y W38 liquidado. Monto final: S/ 57.64.

- **MA-A · Comparación de un pedido.** Pedido 1: mercado S/ 62.50, ahorro S/ 4.86; supermercado S/ 102.75, ahorro S/ 45.11. → MA-01
- **MA-B · Sin precios.** Sin precios de referencia, la comparación del pedido 1 está vacía. Con un pedido todavía sin liquidar, también. → MA-01
- **MA-C · Mi cuenta.** El vecino del pedido 1 ve "Pagaste S/ 61.00", "costó S/ 57.64", "te devolvimos S/ 3.36 a tu saldo", "En el mercado de barrio costaba S/ 62.50: ahorraste S/ 4.86" y "Con Yapa ya te devolvimos S/ 3.36". → MA-02, MA-03
- **MA-D · Más caro que el mercado.** Si la papa blanca del mercado costara S/ 1.00 en vez de S/ 1.50, la canasta costaría S/ 57.50 allá y el vecino ve "pagaste S/ 0.14 más". → S-131
- **MA-E · Pedido no atendido.** Un vecino de Lince cuyo grupo no llegó al mínimo ve "no se atendió" y "te devolvimos S/ 61.00", y el total devuelto es S/ 61.00. → S-130, MA-03
- **MA-F · Mismos números.** `reference_savings` de W38 sigue dando 43.9 % y 7.8 % (iteración 22). → MA-04

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| MA-01, S-131 | `reference.order_comparison`, `reference._basket_reference` | `test_my_savings.test_ma_a_*`, `test_ma_b_*`, `test_ma_d_*` |
| MA-02, S-130 | web `/cuenta` → `views.order_detail`, `views.account` | `test_ma_c_*`, `test_ma_d_*`, `test_ma_e_*` |
| MA-03, S-132 | web `/cuenta` (suma de lo devuelto) | `test_ma_c_*`, `test_ma_e_*` |
| MA-04 | `reference.reference_savings` usa `_basket_reference` | `test_ma_f_*`, `test_reference.test_rf_e_*` |

## Notas

- Al escribir MA-D apareció un empate: dos precios del mismo producto con la misma fecha. La métrica tomaba el primero y el catálogo el último. Ahora los dos toman el **último registrado**, igual que dice S-125.
- Así se ve un pedido liquidado en "Mi cuenta", con los precios de ejemplo: "Pagaste S/ 61.00 · costó S/ 57.64 · te devolvimos S/ 3.36 a tu saldo / En el mercado de barrio costaba S/ 62.50: ahorraste S/ 4.86 / En el supermercado costaba S/ 102.75: ahorraste S/ 45.11".

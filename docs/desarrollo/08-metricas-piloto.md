# Iteración 8 · Métricas del piloto

## Requisito

Como equipo de Yapa, quiero medir cada ciclo liquidado con tres números: la **recompra en la semana 4**, el **margen por pedido** y el **ahorro entregado**. Así sabemos a tiempo si el piloto funciona o si repite los errores de los proyectos que fracasaron.

## Decisiones y fuentes que se aplican

- **Lecciones de los antecedentes (`docs/analisis/05_antecedentes.md`):**
  - L5: la recompra en la semana 4 es la métrica principal del piloto (Muni).
  - L12: cada ciclo debe cerrar con margen positivo (Favo, Muni, Merqueo).
- **`docs/analisis/03_huecos_negocio.md`, H3:**
  - Margen por pedido calculado en cada ciclo, con alerta si un pedido deja margen negativo.
  - Si la recompra en la semana 4 es menor que 50 %, el problema es la propuesta de valor, no el software (Idea v2).
- **`docs/analisis/07_modelo_precios_zonas.md`:** "ningún pedido puede dejar ganancia negativa. El sistema calcula la ganancia por pedido en cada ciclo y la reporta".
- **C-02, C-08, C-09:** el ahorro viene del descuento por volumen y del envío compartido, y vuelve como saldo.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-47 | Solo cuenta como **compra** un pedido `LIQUIDADO`, es decir, atendido y liquidado. Los pedidos cancelados, no atendidos o sin pago verificado no cuentan. | — |
| S-48 | **Recompra en la semana 4.** La cohorte del ciclo N son los vecinos cuya **primera compra** fue en el ciclo N. La recompra es el porcentaje de esa cohorte que compra en el ciclo **N + 3** (la cuarta semana, contando la primera). La meta es **50 %**. | 50 % |
| S-49 | **Margen por pedido** (de contribución) = monto final de la liquidación − reclamos aprobados − costo del proveedor − costo de la parada. El costo del proveedor es el precio base del tramo alcanzado × la cantidad **entregada** (lo que faltó no se le paga). El costo de la parada es el costo de la parada de la zona ÷ los pedidos atendidos de la zona, **sin tope**. No incluye armado, cobro ni atención, porque esos costos siguen en investigación (`08_validacion_economica.md`). | — |
| S-50 | Un pedido con margen **menor que 0** aparece en la lista de alertas del ciclo. Margen 0 no es alerta. | — |
| S-51 | **Ahorro entregado** = ahorro por volumen + ahorro en el envío, en los pedidos liquidados. Ahorro por volumen = (precio máximo − precio final) × cantidad entregada. Ahorro en el envío = envío máximo − envío real. **No** cuenta lo devuelto por faltantes ni por reclamos: eso devuelve lo que no se recibió, no es ahorro. Se calcula con los valores exactos, sin el redondeo del monto final. | — |
| S-52 | Las métricas se calculan solo sobre ciclos ya liquidados. La recompra necesita liquidados el ciclo de la cohorte y el ciclo N + 3. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| MT-01 | Cada métrica necesita el ciclo liquidado (S-52). | `CYCLE_NOT_SETTLED` |
| MT-02 | Margen de cada pedido liquidado del ciclo según S-49, con el detalle de ingreso, costo del proveedor, costo de parada y reclamos. | — |
| MT-03 | Alertas: los pedidos del ciclo con margen negativo (S-50). | — |
| MT-04 | Ahorro entregado del ciclo según S-51: por volumen, en el envío y total. | — |
| MT-05 | Recompra en la semana 4 de la cohorte del ciclo N según S-48: tamaño de la cohorte, cuántos volvieron, porcentaje y si llega a la meta del 50 %. Una cohorte vacía no tiene porcentaje. | `CYCLE_NOT_SETTLED`, `EMPTY_COHORT` |

## Criterios de aceptación

Escenario base: ciclo 2026-W38 con catálogo base. Cada pedido lleva la canasta de la iteración 2 (5 kg de papa amarilla + 10 kg de papa blanca + 10 kg de cebolla roja) y paga S/ 61.00. Con 8 pedidos en Z-JM-01 (parada S/ 40), la papa amarilla y la papa blanca se quedan en el primer tramo y la cebolla llega al tramo desde 80 kg (S/ 1.80 base, S/ 2.016 final). El monto final de cada pedido es S/ 57.64 y el costo del proveedor, S/ 47.00 (5 × 3.60 + 10 × 1.10 + 10 × 1.80).

- **MT-A · Margen normal.** Con los 8 pedidos: ingreso S/ 57.64, costo del proveedor S/ 47.00, parada S/ 5.00 (40 ÷ 8) → margen **S/ 5.64** por pedido y ninguna alerta. → MT-02, MT-03
- **MT-B · Margen negativo.** 8 pedidos en una zona de Jesús María con parada de S/ 100: la parada cuesta S/ 12.50 por pedido, pero el envío cobrado tiene tope de S/ 5 → margen **−S/ 1.86** y los 8 pedidos aparecen en las alertas. → MT-02, MT-03
- **MT-C · Faltante y reclamo.** Un pedido con 2 kg de cebolla faltante: ingreso S/ 53.60, costo del proveedor S/ 43.40 → margen **S/ 5.20**. Otro pedido con un reclamo aprobado de 1 kg de cebolla (S/ 2.02) → margen **S/ 3.62**. → MT-02
- **MT-D · Ahorro con 8 pedidos.** Por volumen: (2.352 − 2.016) × 10 kg de cebolla × 8 pedidos = **S/ 26.88**; en el envío: S/ 0 (5 − 5) → total **S/ 26.88**. → MT-04
- **MT-E · Ahorro con 20 pedidos.** Se alcanzan los tramos desde 100 kg de las papas y desde 200 kg de la cebolla, y el envío baja a S/ 2 → por volumen **S/ 197.12**, en el envío **S/ 60.00**, total **S/ 257.12**. → MT-04
- **MT-F · Recompra que llega a la meta.** 8 vecinos compran por primera vez en W38 (además, un grupo de 7 pedidos de Lince no se atiende y no entra en la cohorte). En W41, 5 de esos 8 vuelven a comprar junto con 3 vecinos nuevos → cohorte 8, volvieron 5, **62.5 %**, llega a la meta. → MT-05, S-47
- **MT-G · Recompra bajo la meta.** En W41 vuelven 3 de los 8, con 5 vecinos nuevos → **37.5 %**, no llega a la meta. → MT-05
- **MT-H · Sin liquidar o sin cohorte.** Pedir el margen, el ahorro o la recompra de un ciclo sin liquidar → `CYCLE_NOT_SETTLED`; la recompra con W41 sin liquidar → `CYCLE_NOT_SETTLED`; la recompra de un ciclo liquidado sin compras → `EMPTY_COHORT`. → MT-01, MT-05

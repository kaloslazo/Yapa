# Iteración 68 · Predicción de demanda

## Requisito

Como encargado de compras, quiero ver cuánto se va a pedir de cada producto en la semana, antes del cierre del miércoles, para pedirle al mayorista una cotización con cantidades realistas y saber si el máximo del catálogo se va a quedar corto.

## Por qué

La propuesta del curso pide IA en el producto: "predicción de demanda: modelo básico de machine learning (regresión sobre histórico de pedidos) para estimar la canasta semanal por zona y ajustar cotizaciones con el mayorista antes del cierre". Hasta la iteración 67 el panel solo mostraba lo ya pedido.

## Alcance

Cálculo de lectura en el motor (biblioteca estándar, sin servicios externos ni costo) y una tarjeta en Compra de la semana. No cambia precios, máximos ni pedidos: la predicción es una ayuda para cotizar.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-339 | La historia son las 8 semanas anteriores a la semana que se predice. Una zona entra en la serie desde la primera semana en que pidió; antes de eso no cuenta como cero. | 8 semanas |
| S-340 | Con 3 o más semanas de historia se ajusta una recta por mínimos cuadrados (tendencia) y se lee en la semana siguiente; con 1 o 2, el promedio; sin historia no hay estimado. Nunca negativo. | — |
| S-341 | La demanda es lo pedido (sin cancelados), aunque el grupo no llegue al mínimo: eso también es demanda que el mayorista debe conocer. | — |
| S-342 | El estimado por producto es la suma de los estimados por zona, redondeada hacia arriba al paso del producto. | — |
| S-343 | Se puede cargar historia previa a Yapa (por ejemplo, la planilla del piloto) en `demand_history` por (semana, zona, producto). La demo la siembra con 6 semanas ficticias. | — |
| S-344 | Si la semana ya cerró, se compara el estimado con lo pedido y se muestra el error porcentual medio de los productos con pedido. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| PD-01 | `GET /api/compras` trae `prediccion` para la semana elegida: por producto `id`, `nombre`, `unidad`, `historia` (8 números, de la más antigua a la más reciente), `estimado`, `pedido`, `maximo`, `supera_maximo` y `metodo` (`tendencia`, `promedio` o `sin_historia`). | — |
| PD-02 | Por zona: `zonas` con `id`, `nombre` y los productos con estimado mayor que cero. | — |
| PD-03 | `supera_maximo` es verdadero si el estimado pasa el máximo del catálogo de la semana: hay que pedir más al mayorista. | — |
| PD-04 | Con la semana cerrada, `error_medio` es el promedio de abs(estimado − pedido) / pedido de los productos con pedido; con la semana abierta es `null`. | — |
| PD-05 | Solo admin y compras (como el resto de `/api/compras`). | `NOT_AUTHORIZED` (403) |

## Criterios de aceptación

Escenario base: zona Z-LINCE-01 pidió papa amarilla 10, 12, 14 y 16 kg en las 4 semanas anteriores; Z-JM-01 pidió 5 kg solo la semana anterior.

- **PD-A · Tendencia.** Z-LINCE-01 estima 18 kg (recta exacta); Z-JM-01 estima 5 kg (promedio de 1 semana). Papa amarilla: 23 kg, método `tendencia`. → PD-01, S-340, S-342
- **PD-B · Historia.** La `historia` de papa amarilla es `[0, 0, 0, 0, 10, 12, 14, 21]`. → PD-01, S-339
- **PD-C · Zona que empieza.** Una zona sin pedidos antes no baja la recta de otra: Z-LINCE-01 sigue en 18. → S-339
- **PD-D · Cancelados.** Un pedido cancelado de 100 kg en la semana anterior no cambia el estimado. → S-341
- **PD-E · Máximo.** Con máximo de catálogo 20 kg, papa amarilla trae `supera_maximo` verdadero. → PD-03
- **PD-F · Redondeo.** Una zona nueva que pidió 2 y 2.6 galones estima 2.3 de un producto con paso 1 sale 3. → S-342
- **PD-G · Nunca negativo.** Una serie 9, 6, 3 (recta a 0) y otra 9, 5, 1 (recta a −3) estiman 0. → S-340
- **PD-H · Error.** Semana cerrada con 20 kg pedidos y 23 estimados: `error_medio` 0.15. Semana abierta: `null`. → PD-04
- **PD-I · Historia importada.** 12 kg cargados en `demand_history` cuentan como pedidos de esa semana y zona. → S-343
- **PD-J · Permiso.** Un vecino recibe 403 en `/api/compras`. → PD-05
- **PD-K · Pantalla.** Compra de la semana muestra la tarjeta "Lo que se viene" con el estimado, lo ya pedido y el aviso "pide más al mayorista" cuando supera el máximo. → PD-01, PD-03

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| PD-01 | `forecast.forecast` y `forecast.predict`; `web/api.py` `compras` (`prediccion`) y `forecast_json` | `test_prediccion_68.test_pd_a_*`, `test_pd_b_*`, `test_pd_01_*` |
| PD-02 | `forecast.forecast` (`zonas`) | `test_pd_a_*`, `test_pd_c_*` |
| PD-03 | `supera_maximo` en `forecast.forecast` | `test_pd_e_*` |
| PD-04 | `error_medio` en `forecast.forecast` | `test_pd_h_*` |
| PD-05 | ruta `/api/compras` con `BUYING` | `test_pd_j_*` |
| S-339 | `WEEKS` y `zones_first` | `test_pd_b_*`, `test_pd_c_*` |
| S-340 | `forecast.predict` | `test_pd_a_*`, `test_pd_f_*`, `test_pd_g_*`, `test_without_history_*` |
| S-341 | `forecast.weekly_demand` | `test_pd_d_*` |
| S-342 | `forecast._round_up` | `test_pd_f_*` |
| S-343 | `store.demand_history`; `demo.seed_demand_history` | `test_pd_i_*` |
| PD-K | `Forecast` en `AdminPanel.tsx` (Compra de la semana) y estilos `.forecast-*` | `src/components/prediccion.test.ts` |

## Evidencia

- `68-motor-rojo.txt` y `68-web-rojo.txt`: las pruebas fallan antes del código (no existía `forecast`; la tarjeta no aparecía).
- `68-motor-verde.txt` y `68-web-verde.txt`: motor, TypeScript, web y build en verde.
- En la demo local (semana del 16 al 22 de noviembre, abierta), Compra de la semana estima 60 kg de papa amarilla con 30 kg ya pedidos, y muestra la historia de 8 semanas en barras.

## Cómo es IA y cuánto cuesta

Es un modelo de regresión lineal (aprendizaje supervisado sobre la serie de cada zona) calculado en el propio motor con la biblioteca estándar: no usa servicios externos, no tiene costo por consulta y funciona sin claves. Con la semana cerrada, el error medio sirve para ver si conviene cambiar el modelo (por ejemplo, a uno con estacionalidad) cuando haya más semanas reales.

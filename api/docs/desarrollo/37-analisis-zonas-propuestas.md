# Iteración 37 · Análisis por zona y propuestas del sistema

## Requisito

Como admin de Yapa, quiero ver cómo va cada zona (pedidos, avance, ganancia), qué zonas se pueden unir hoy y qué me propone el sistema para llegar al mínimo, vender más y detectar zonas que pierden plata, sin tener que cruzar tablas a mano.

## Por qué

Pedido del equipo (18/10/2026): ver el panel de admin "como empresa": ganancias por zona, análisis de datos, qué propone el sistema (marketing, fusiones) y ver las zonas en un mapa. El motor ya sabe unir zonas (pide un admin, acepta el otro, a 500 m o menos, con el ciclo abierto), pero el admin de Yapa no ve qué uniones convienen ni por qué una no se puede.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-182 | **Adopción de una zona** = pedidos de la semana (sin cancelados) entre vecinos de la zona, en porcentaje entero. | % |
| S-183 | **Propuesta de unir.** Se propone unir dos grupos cuando el motor permite la unión hoy (a 500 m o menos, ciclo abierto), al menos uno no llega al mínimo, y juntos sí llegan con sus pedidos verificados. | mínimo 8 |
| S-184 | **Propuesta de recordar.** Una zona que no llega al mínimo y donde los vecinos que aún no pidieron bastarían para llegar (verificados + faltantes ≥ 8). | mínimo 8 |
| S-185 | **Propuesta de invitar.** Una zona activa con menos vecinos que el mínimo: aunque todos pidan, no llega. Se sugiere que su admin invite (premio por referido de S/ 3 + S/ 3, ya aprobado en la iteración 28). | mínimo 8 |
| S-186 | **Propuesta de revisar costo.** En una semana ya liquidada, una zona cuyo margen total es negativo. | margen < 0 |
| S-187 | **Propuesta de reactivar.** Vecinos que recibieron su pedido la semana anterior y aún no piden en la semana en curso. Se muestra solo si son 1 o más. | 1 o más |
| S-188 | **Demo con dos admins de zona.** La demo suma un tercer edificio de Lince (Edificio Arenales, admin Marta Quispe, cliente 116) a 391 m de Los Álamos y 455 m de Las Palmeras, para poder ver la unión con acuerdo de los dos admins. No tiene pedidos ni afecta los números de la semana. | 1 zona, 1 vecino |
| S-189 | Las propuestas son **sugerencias**: el sistema no ejecuta nada solo. Cada una dice qué datos la originan. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AN-01 | `GET /api/admin/analisis?ciclo=` (solo admin) devuelve `zonas`, `uniones` y `propuestas` de la semana pedida (por defecto la actual). | `LOGIN_REQUIRED`, `FORBIDDEN` |
| AN-02 | Cada zona trae: nombre, distrito, grupo, estado, ubicación, vecinos, pedidos, verificados, adopción (S-182) y margen de la semana. El margen es `null` si la semana no se liquidó. | — |
| AN-03 | `uniones` lista cada par de zonas de grupos distintos a 500 m o menos, con la distancia en metros y `motivo`: vacío si se puede unir hoy, o el código que la bloquea (`CYCLE_CLOSED`, `ZONES_TOO_FAR`, `LOCATION_REQUIRED`). Las zonas sin ubicación no entran. | — |
| AN-04 | `propuestas` sigue S-183 a S-187. Cada propuesta trae `tipo` (`UNIR`, `RECORDAR`, `INVITAR`, `REVISAR_COSTO`, `REACTIVAR`), las zonas que involucra, un `titulo`, un `detalle` en palabras y los `datos` que la originan. | — |
| AN-05 | Orden de las propuestas: primero las que ayudan a llegar al mínimo (UNIR, RECORDAR, INVITAR), luego REVISAR_COSTO y REACTIVAR. Dentro de cada tipo, por nombre de zona. | — |
| AN-06 | Sin pedidos ni ventas esa semana el análisis responde igual (zonas con ceros, sin propuestas de dinero). Un ciclo con formato inválido da el mismo error que las demás pantallas del admin. | `INVALID_CYCLE` |
| AN-07 | Consultar el análisis no cambia nada: no mueve dinero ni zonas. | — |
| AN-08 | `merge_blocker(store, zona, destino, ahora)` devuelve el código que impide unir hoy o `None`. Usa las mismas reglas que pedir y aceptar la unión (no las duplica). | — |

## Criterios de aceptación (`tests/test_analisis.py`)

Escenario base: semana abierta 2026-W38 (miércoles 16/09/2026 10:00). Zonas del piloto (Los Álamos ya trae 3 vecinos) más un edificio extra en Lince a 391 m de Los Álamos. La propuesta de invitar y la de recordar se calculan por grupo de zonas unidas.

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| AN-A | Solo el admin | vecino 101 o sin sesión | 403 `FORBIDDEN` y 401 `LOGIN_REQUIRED` |
| AN-B | Datos de zona | Los Álamos con 9 vecinos, 5 pidieron y 4 pagaron verificado | pedidos 5, verificados 4, adopción 56 |
| AN-C | Margen sin liquidar | semana abierta | `margen` es `null` |
| AN-D | Unión posible | Arenales (grupo propio) y Los Álamos a 391 m, ciclo abierto | par con distancia 391 y motivo vacío |
| AN-E | Unión bloqueada por ciclo | mismo par, sábado 19/09 | motivo `CYCLE_CLOSED` |
| AN-F | Sin pares lejanos | Miraflores a más de 500 m | no aparece en `uniones` |
| AN-G | Propuesta de unir | Álamos con 4 verificados y Arenales con 4 verificados | propuesta `UNIR` con 8 en total |
| AN-H | No se propone si juntas no llegan | 2 y 3 verificados | sin propuesta `UNIR` |
| AN-I | Recordar | Álamos con 4 verificados y 4 vecinos sin pedir | propuesta `RECORDAR` con 4 sin pedir |
| AN-J | Invitar | zona activa con 5 vecinos | propuesta `INVITAR` con el dato 5 vecinos |
| AN-K | Costo | semana liquidada con una zona de margen negativo | propuesta `REVISAR_COSTO` con el margen |
| AN-L | Reactivar | 3 vecinos recibieron en W37 y no piden en W38 | propuesta `REACTIVAR` con 3 |
| AN-M | Orden | hay UNIR y REACTIVAR a la vez | UNIR sale antes |
| AN-N | Sin datos | ciclo sin pedidos | 200, zonas con ceros |
| AN-O | Ciclo inválido | `?ciclo=hola` | 422 `INVALID_CYCLE` |
| AN-P | No cambia nada | consultar dos veces | las zonas y el dinero (`money_balance`) quedan igual |
| AN-R | Datos para el mapa | consultar el análisis | trae `radio_m` 300, `union_m` 500 y la lista de semanas conocidas con la actual |
| AN-S | Fuera del piloto | Miraflores con 1 vecino | no genera propuesta |
| AN-T | Singular | una zona con 1 vecino | el detalle dice "Tiene 1 vecino" |
| AN-Q | Demo | `demo_store()` | existe `Z-LINCE-03` con admin 116 a 391 m de `Z-LINCE-01`, y los números de la semana no cambian |

## Trazabilidad (regla → código → prueba)

| Regla | Código | Prueba |
|---|---|---|
| AN-01, AN-07 | `admin_analisis` en `src/yapa_sdd/web/api.py`, `insights.analysis` | AN-A, AN-P |
| AN-02 | `_zone_rows` en `src/yapa_sdd/insights.py` | AN-B, AN-C |
| AN-03 | `_unions` | AN-D, AN-E, AN-F |
| AN-04, AN-05 | `_propose_merges`, `_propose_for_groups`, `_propose_money`, orden en `analysis` | AN-G..AN-M |
| AN-06 | `query_cycle` (ya existente) y ceros sin pedidos | AN-N, AN-O |
| AN-09 | La respuesta incluye `radio_m` (300), `union_m` (500) y `ciclos` (semanas conocidas, como las demás pantallas del admin) para dibujar el mapa y elegir semana. | — |
| AN-10 | Las propuestas de unir, recordar e invitar solo cuentan zonas de los distritos del piloto (Lince, Jesús María y La Victoria). | — |
| AN-11 | Los textos usan singular y plural correctos ("1 vecino", "2 vecinos"). | — |
| AN-08 | `merge_blocker` en `src/yapa_sdd/zones.py` | AN-D, AN-E |
| S-188 | zona y vecino nuevos en `src/yapa_sdd/demo.py`, PIN de demo en `web/__main__.py` | AN-Q |

Evidencia: `docs/evidencia/desarrollo/37-analisis-rojo.txt` (17 fallas y 1 error antes del código) y `37-analisis-verde.txt` (364 pruebas, 18 nuevas).
Cuenta demo nueva: Marta Quispe, cliente 116, PIN 260318 (solo demo local).

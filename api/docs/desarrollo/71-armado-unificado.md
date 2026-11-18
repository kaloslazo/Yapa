# Iteración 71 · Revisión de productos por bolsa y baja de una bolsa

> **Reescrita el 18/11/2026** con el formato de las demás specs (la versión del 17/11 tenía las reglas en un párrafo y los supuestos en un rango sin detalle). Las reglas y las pruebas son las mismas.
>
> **Cambiada por la iteración 76.** Esta iteración hizo que la foto de la bolsa pasara primero por el detector y que la bolsa se guardara recién al confirmar cada fila. Eso contradice S-331 y OC-G de la iteración 64 ("al elegir la foto, se registra la bolsa sin otro toque") y se hizo cambiando la prueba de OC-G sin tocar la spec de la 64. La 76 lo devolvió: la bolsa se guarda con la foto y el detector se usa a pedido. Siguen vigentes AR71-2 a AR71-5.

## Requisito (Aaron, 17/11/2026)

Como armador, quiero anotar qué productos y cuántas unidades se ven en la foto de cada bolsa y poder quitar una bolsa que registré por error antes de que salga el reparto.

## Supuestos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-357 | Una foto es una bolsa. | — |
| S-358 | Las unidades que se ven en la foto nunca se pasan a kilos: el peso se revisa aparte. | — |
| S-359 | Si el pedido tiene una sola variedad de papa, lo que el detector llama "papa" se asigna a esa; con papa blanca y amarilla, se elige a mano. | — |
| S-360 | Quitar una bolsa se puede antes del despacho. La foto no se borra, queda un registro (quién, cuándo y qué revisión tenía) y su número no se vuelve a usar. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AR71-1 | *(Reemplazada por AR76-1 y AR76-7.)* Elegir la foto la mandaba al detector; la bolsa se guardaba al confirmar las filas. | — |
| AR71-2 | La revisión de una bolsa son filas con un producto del pedido y unidades enteras de 1 a 300, como máximo 30. Se guarda con la bolsa (`bag_reviews`) y la pantalla de armado la devuelve en `bolsas[].productos`. | `INVALID_BAG_REVIEW` |
| AR71-3 | Cada foto nueva es otra bolsa. El número sigue aunque se haya quitado una. | — |
| AR71-4 | `POST /api/admin/bolsas/quitar` con `pedido` y `numero` quita la bolsa (la pantalla pide confirmar). No se puede si la zona salió a reparto, se entregó, falló o la semana se liquidó. | `ZONE_ALREADY_CLOSED`, `BAG_NOT_FOUND` |
| AR71-5 | Antes del cierre (miércoles 8 p. m.) no se arma. | `CYCLE_STILL_OPEN` |

## Criterios de aceptación

Escenario base: 8 pedidos de Residencial San Felipe, viernes 18/09/2026 10:00.

- **AR71-A · Revisión y números.** Bolsa 1 con `[PAPA-AMARILLA ×2]`, bolsa 2 sin revisión; se quita la 1 y la siguiente es la 3. Queda 1 registro de baja con la foto `uno.jpg`, también después de guardar y abrir la base. → AR71-2..AR71-4, S-360
- **AR71-B · Revisión inválida.** `NO-EXISTE`, 0 unidades o 1.5 unidades dan `INVALID_BAG_REVIEW` y no se guarda ninguna bolsa. → AR71-2
- **AR71-C · Zona despachada y semana abierta.** Con la zona despachada no se quita (`ZONE_ALREADY_CLOSED`) y antes del cierre no se arma (`CYCLE_STILL_OPEN`). → AR71-4, AR71-5
- **AR71-D · Bolsa que no existe.** Bolsa 99 → `BAG_NOT_FOUND`. → AR71-4
- **AR71-E · Papa ambigua.** Con papa blanca y amarilla en la lista, la fila "papa ×3" queda sin producto y no se guarda hasta elegir cuál. → S-359

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| AR71-2 | `fulfillment._clean_review` y `pack_bag`; `web/api.py` `bag_review` y `admin_bolsa` | `test_armado71.test_ar71_a_*`, `test_ar71_b_*` |
| AR71-3, AR71-4, S-360 | `fulfillment.remove_bag`, `_open_bag`, `bag_counters`, `bag_removals`; ruta `/api/admin/bolsas/quitar` | `test_ar71_a_*`, `test_ar71_c_*`, `test_ar71_d_*` |
| AR71-5 | `pack_bag` (`CYCLE_STILL_OPEN`) | `test_ar71_c_*` |
| S-359 | `utils/photoMatches.ts` (`matchPhotoProduct`) | `photoMatches.test.ts`, `PhotoProductReview.test.ts` ("exige elegir la variedad de papa") |
| Pantalla | `PackCard` en `AdminPanel.tsx` (bolsas con "Quitar bolsa") | `operacionCelular.test.ts` |

## Evidencia

`71-armado-rojo.txt`, `71-armado-motor-verde.txt` y `71-armado-web-verde.txt` (17/11/2026, en la máquina de Aaron).

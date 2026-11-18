# Iteración 76 · La bolsa se guarda con la foto y el detector se usa cuando se pide

## Requisito

Como armador, quiero que la bolsa quede registrada apenas tomo su foto, como en la iteración 64, y usar el detector de productos solo si me ayuda. Como proveedor, quiero lo mismo al contar una carga.

## Por qué

1. **La iteración 71 cambió una regla de otra iteración sin pasar por su spec.** S-331 y el criterio OC-G de la iteración 64 dicen que "al elegir la foto, se registra la bolsa sin otro toque". La 71 hizo que la foto pase primero por el detector y que la bolsa se guarde recién después de confirmar cada fila, y cambió la prueba de OC-G para que exija lo contrario (`operacionCelular.test.ts`). La spec de la 64 no se tocó.
2. **El detector se equivoca más de lo que acierta con nuestros productos.** Su README da 56,6 % de precisión y 57 % de mAP50 en su propio test. El 18/11/2026 se pasaron por `/api/vision/analizar` las 16 fotos del catálogo (`public/images/products`):

| Foto | El detector dice | ¿Bien? |
|---|---|---|
| Papa amarilla | papa ×4 | sí |
| Cebolla roja | cebolla ×3 | sí |
| Ajo | cebolla ×3, ajo ×1 | a medias |
| Papa blanca | cebolla ×1 | no |
| Zanahoria | papa ×4, zanahoria ×2 | no |
| Camote | papa ×4, cebolla ×1 | no |
| Tomate italiano | cebolla ×2 | no |
| Limón | cebolla ×2 | no |
| Plátano de seda | zanahoria ×2 | no |
| Leche en pack | cebolla ×2 | no |
| Limpiatodo | ajo ×1, zanahoria ×1 | no |
| Aceite, arroz, detergente, lavavajillas, lejía | nada | sí |

   Con el detector en automático, cada foto llena filas que el armador tiene que borrar o corregir antes de poder guardar la bolsa: la parte más repetida del armado quedó más lenta.

## Alcance

Solo pantalla y una ruta nueva para guardar la revisión de una bolsa ya registrada. No cambia pesos, precios, pagos, saldo ni el catálogo. El detector y el stock del proveedor se conservan.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-369 | Elegir la foto de la bolsa la registra sin otro toque (vuelve S-331). El detector no corre solo. | — |
| S-370 | Después de registrar una bolsa, su tarjeta ofrece "Revisar la foto con el detector (opcional)" para esa foto. Al recargar la página ya no se ofrece para las bolsas anteriores. | — |
| S-371 | Solo se muestran sugerencias que corresponden a un producto del pedido (Armado) o de la lista del proveedor (Stock). Las demás se descartan y se dice cuántas. | — |
| S-372 | La revisión confirmada se guarda en la bolsa ya registrada y reemplaza la anterior de esa bolsa. Se puede mientras la zona no salga a reparto ni se cierre. Lleva entre 1 y 30 filas. | 1..30 |
| S-373 | En Stock del proveedor el detector también se usa a pedido; confirmar la carga sigue pidiendo filas y peso medido (ST72). | — |
| S-374 | Se retira el selector de varias bolsas (`BagForm`, iteración 75), que desde la 71 ya no aparecía en ninguna pantalla. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AR76-1 | En Armado, elegir la foto manda `POST /api/admin/bolsas` con el pedido y la foto; no llama al detector. | — |
| AR76-2 | `POST /api/admin/bolsas/revision` con `pedido`, `numero` y `revision` guarda la revisión de esa bolsa. | — |
| AR76-3 | Revisión vacía, con más de 30 filas, con un producto que no es del pedido o con unidades fuera de 1..300. | `INVALID_BAG_REVIEW` |
| AR76-4 | La bolsa no existe (o se quitó). | `BAG_NOT_FOUND` |
| AR76-5 | La zona ya salió a reparto, se entregó, falló o la semana se liquidó. | `ZONE_ALREADY_CLOSED` |
| AR76-6 | Solo quien arma (armador o admin). | `NOT_AUTHORIZED` / 403 |
| AR76-7 | El detector corre solo al tocar "Sugerir con el detector" y descarta lo que no está en el pedido o en la lista. | — |

## Criterios de aceptación

Escenario base: 8 pedidos de Residencial San Felipe, viernes después del cierre; el armador arma el primer pedido.

- **AR76-A · Un toque (OC-G).** En la tarjeta del pedido 13, elegir la foto manda `/api/admin/bolsas` con `pedido = 13` y la foto; `/api/vision/analizar` no se llama. → AR76-1, S-369
- **AR76-B · Revisión guardada.** Con la bolsa 1 registrada, guardar la revisión `[PAPA-AMARILLA ×2]` la deja en `bag_reviews` y `/api/admin/armado` la muestra en `bolsas[0].productos`. Guardar `[PAPA-AMARILLA ×3]` la reemplaza. → AR76-2, S-372
- **AR76-C · Revisión inválida.** `[]`, un producto que no es del pedido o 0 unidades dan `INVALID_BAG_REVIEW` y no cambian la revisión anterior. → AR76-3
- **AR76-D · Bolsa que no existe.** Bolsa 99 → `BAG_NOT_FOUND`. → AR76-4
- **AR76-E · Zona cerrada.** Con la zona despachada → `ZONE_ALREADY_CLOSED`. → AR76-5
- **AR76-F · Permiso.** Un vecino recibe 403. → AR76-6
- **AR76-G · Detector a pedido y filtrado.** Tras registrar la bolsa, la tarjeta muestra "Revisar la foto con el detector (opcional)". Al tocar "Sugerir con el detector" con la respuesta `papa ×2, cebolla ×3` en un pedido sin cebolla, aparece una sola fila (Papa amarilla, 2) y el aviso "1 sugerencia no está en el pedido". Confirmar la fila y guardar manda `/api/admin/bolsas/revision` con `numero = 1`. → AR76-7, S-370, S-371
- **AR76-H · Stock a pedido.** En Stock del proveedor, elegir la foto no llama al detector; tocar "Sugerir con el detector" sí. → S-373

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| AR76-1, S-369 | `PackCard` y `saveBag` en `AdminPanel.tsx` (la cámara sube al elegir la foto) | `operacionCelular.test.ts` (OC-G, de vuelta a su versión de la 64), `armado76.test.ts` (AR76-G) |
| AR76-2, S-372 | `fulfillment.review_bag` y `_open_bag`; `web/api.py` `admin_bolsa_revision` y la ruta `/api/admin/bolsas/revision` | `test_armado76.test_ar76_b_*` (motor y API) |
| AR76-3 | `fulfillment._clean_review` (compartida con `pack_bag`) y `bag_review` en la API | `test_ar76_c_*` |
| AR76-4 | `_open_bag` (`BAG_NOT_FOUND`) | `test_ar76_d_*` |
| AR76-5 | `_check_bag_open` (compartida con `remove_bag`) | `test_ar76_e_*` |
| AR76-6 | ruta con `PACKING` y `check_role` | `test_ar76_f_*` |
| AR76-7, S-370, S-371 | `PhotoProductReview.tsx` (`pick` sin detector, `suggest` a pedido, `keepKnown` descarta lo que no está) y el desplegable `.pack-review` | `armado76.test.ts` (AR76-G), `PhotoProductReview.test.ts`, `operations.test.ts` (PA-02) |
| S-373 | `SupplierStock.tsx` con `scope="tu lista"` | `armado76.test.ts` (AR76-H), `stock72.test.ts` (ST72-G) |
| S-374 | `BagForm.tsx`, `BagForm.test.ts` y los estilos `.bag-*` borrados | — |

Pruebas que cambiaron por esta spec (no se debilitaron: piden lo nuevo):

- `operacionCelular.test.ts` OC-G vuelve a la versión de la iteración 64, que la 71 había cambiado para exigir lo contrario.
- `operations.test.ts` PA-02 pedía un revisor del detector en cada tarjeta; ahora pide la cámara y ningún revisor antes de guardar una bolsa.
- `PhotoProductReview.test.ts` y `stock72.test.ts` tocan "Sugerir con el detector" antes de esperar sugerencias.

Revisado en el navegador con la demo (viernes de armado, `armado-demo`): elegir la foto registró la bolsa 1 del pedido 110 sin llamar al detector; "Sugerir con el detector" devolvió papa ×4 sin producto asignado (el pedido tiene papa blanca y amarilla, S-359); al elegir Papa amarilla y guardar, `/api/admin/armado` devuelve la bolsa con `[PAPA-AMARILLA ×4]` y la lista del pedido la marca.

## Evidencia

- `76-motor-rojo.txt` y `76-web-rojo.txt`: las pruebas fallan antes del código.
- `76-motor-verde.txt` y `76-web-verde.txt`: motor, TypeScript, web y build en verde.

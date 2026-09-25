# Iteración 21 · Huecos del armado, el colchón y el catálogo

## Requisito

Como Yapa, quiero cerrar los huecos que quedaron abiertos en las iteraciones 6 y 7, para que el armado y la reposición dejen un registro claro y el catálogo no acepte datos que después fallan.

## Huecos que se cierran

| Hueco | Dónde se anotó | Qué pasaba |
|---|---|---|
| Bolsas después de entregar | iteración 7, hueco 3 | Se podían registrar bolsas de un pedido cuya zona ya se entregó o falló. |
| Uso del colchón sin pedido | iteración 7, hueco 4 | Al reponer con el colchón no quedaba a qué pedido fue. |
| Unidad del producto | iteración 6, hueco 3 | Un producto con otra unidad (por ejemplo `caja`) se publicaba. El paso ya se validó en la iteración 20 (S-120). |
| Proveedor que deja de ser aliado | iteración 6, hueco 4 | No había regla. |

El hueco 2 de la iteración 6 (desactivar en el catálogo base) se cerró en la iteración 20 (S-118).

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-121 | Cuando una zona ya se entregó o se registró como fallida, no se registran más bolsas de sus pedidos. Si falta algo, va por reclamo. | — |
| S-122 | Cada uso del colchón indica **a qué pedido** se repone. El pedido tiene que atenderse en el ciclo y tener ese producto. Lo repuesto a un pedido, sumado entre usos, no pasa de lo que pidió. Se guarda el registro: pedido, producto, cantidad, valor que sale del colchón, quién y cuándo. | — |
| S-123 | La unidad de un producto es `kg` o `unidad`. Para `unidad`, el paso es un número entero (no se vende medio galón). | — |
| S-124 | Si un proveedor deja de ser aliado a mitad de semana, el catálogo publicado **no cambia**: se respeta el precio que vio el vecino (C-01). El admin decide si desactiva sus productos (CT-09). Desde el catálogo siguiente, sus productos ya no se pueden publicar (CT-02). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AR-06 | No se arma un pedido cuya zona ya se entregó o falló en el ciclo (S-121). | `ZONE_ALREADY_CLOSED` |
| CO-06 | Usar el colchón exige un pedido que existe y se atiende (S-122). | `ORDER_NOT_FOUND`, `ORDER_NOT_ATTENDED` |
| CO-07 | El pedido tiene el producto, y lo repuesto (sumando usos anteriores) no pasa de lo pedido (S-122). | `BUFFER_NOT_FOR_ORDER` |
| CO-08 | Cada uso queda registrado con pedido, producto, cantidad, valor, quién y cuándo. La pantalla del colchón lo muestra (S-122). | — |
| CT-12 | La unidad es `kg` o `unidad`; con `unidad`, el paso es entero (S-123). | `INVALID_UNIT` |

## Criterios de aceptación

Escenario: 8 pedidos de Jesús María del ciclo 2026-W38 con la canasta de prueba, más un pedido 9 con 4 galones de limpiatodo y 5 kg de papa amarilla (S/ 54.60; solo con el limpiatodo no llegaba al pedido mínimo de S/ 50). El colchón tiene 6 galones de limpiatodo (S/ 47.40).

- **HC-A · Bolsa después de entregar.** Se arman los pedidos y se entrega la zona. Registrar otra bolsa del pedido 1 → `ZONE_ALREADY_CLOSED`. Lo mismo en una zona con entrega fallida. → AR-06
- **HC-B · Reponer a un pedido.** Se usan 2 galones para el pedido 9 → quedan 4 (S/ 31.60) y hay un registro: pedido 9, limpiatodo, 2, S/ 15.80, `admin-yapa`, con su hora. → CO-06, CO-08
- **HC-C · Límite por pedido.** Con 2 ya repuestos al pedido 9, reponer 3 más → `BUFFER_NOT_FOR_ORDER` (2 + 3 = 5 > 4). Reponer 2 más sí se acepta. → CO-07
- **HC-D · Pedido sin ese producto.** Reponer limpiatodo al pedido 1 (no lo pidió) → `BUFFER_NOT_FOR_ORDER`. → CO-07
- **HC-E · Pedido inválido.** Pedido 999 → `ORDER_NOT_FOUND`. El mismo pedido en Lince, donde el grupo no llega al mínimo → `ORDER_NOT_ATTENDED`. → CO-06
- **HC-F · Web.** En `/admin/colchon`, el formulario de reponer pide el número de pedido, y la pantalla muestra el uso ("Pedido 9"). → CO-08
- **HC-G · Unidad.** Publicar un producto con unidad `caja` → `INVALID_UNIT`. Uno con unidad `unidad` y paso 0.5 → `INVALID_UNIT`. Con `kg` y paso 0.25 se acepta. → CT-12
- **HC-H · Proveedor que deja de ser aliado.** Con el catálogo de W39 publicado, el proveedor de frescos deja de ser aliado el lunes → la papa amarilla sigue en el catálogo de W39 y un vecino puede pedir 10 kg de papa y 2 galones de limpiatodo (S/ 61.42; el máximo por vecino es 10 kg por producto). Publicar W40 con ese proveedor → `SUPPLIER_NOT_ALLIED`. → S-124

## Cambios en pruebas anteriores

- CO-D, CO-E (`test_fulfillment`) y OA-11 (`test_web_operacion`) usaban el colchón sin indicar pedido. Por S-122, ahora indican un pedido con limpiatodo (con papa amarilla para llegar al mínimo). Los números que verifican no cambian.

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| AR-06, S-121 | `fulfillment.pack_bag` | `test_gaps_packing.test_hc_a_*` |
| CO-06, CO-07, S-122 | `buffer.use_buffer` (pedido, atención, lo ya repuesto) | `test_hc_c_*`, `test_hc_d_*`, `test_hc_e_*`, `test_fulfillment.test_co_d_*` |
| CO-08 | `buffer.BufferUse`, `store.buffer_uses` · web `/admin/colchon` (campo pedido y tabla de reposiciones) | `test_hc_b_*`, `test_hc_f_*`, `test_web_operacion.test_oa11_*` |
| CT-12, S-123 | `catalog.UNITS`, `catalog._check_product` | `test_hc_g_*` |
| S-124 | sin código nuevo: el catálogo publicado no se vuelve a validar; CT-02 aplica al siguiente | `test_hc_h_*` |

## Notas

- Al escribir las pruebas, dos pedidos del escenario rompían reglas que ya existían: el pedido mínimo de S/ 50 y el máximo de 10 kg por producto por vecino. Se corrigió el escenario en la spec antes que las pruebas; el código no cambió por eso.
- Sigue abierto el hueco 4 de la iteración 8: el valor que sale del colchón todavía no aparece como costo en el margen del pedido. Ahora ya se sabe a qué pedido fue (`buffer_uses`), así que se puede sumar cuando el equipo lo decida.

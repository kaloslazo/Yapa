# Iteración 7 · Armado, entrega en portería, reclamos por artículo y colchón de reposición

## Requisito

Como Yapa, quiero dejar evidencia de cada bolsa que armo y de cada entrega en el punto de recepción, para saber qué pasó si algo se pierde en la portería o en manos del cliente. Con la entrega termina mi responsabilidad.

Como vecino, quiero reclamar un artículo que me llegó dañado o que faltó, dentro de las 24 horas siguientes a la entrega, y que me devuelvan solo ese artículo.

Como Yapa, quiero guardar un colchón pequeño de sobrantes no perecibles para reponer faltantes, pero con un tope de monto para no convertirme en almacén.

## Decisiones del equipo que se aplican

- **Carlos, 24/09 (`docs/analisis/07_modelo_precios_zonas.md`, punto 6):**
  - Foto del contenido de **cada bolsa** al terminar de armarla.
  - Foto de la entrega y registro de **quién recibe** y a qué hora.
  - Con esa entrega termina la responsabilidad de Yapa.
  - El plazo para reportar daños o faltantes corre desde la entrega.
- **C-10:** los artículos faltantes o dañados se devuelven **por artículo**, no por pedido completo.
- **C-05 y LQ-08:** lo que Yapa devuelve vuelve como **saldo** ("te devolvemos").
- **Punto 8 (aprobado):** colchón de reposición **con tope de monto**, solo con no perecibles. El documento da S/ 500 como ejemplo.
- **C-07 y S-28:** la zona tiene un punto de recepción (portería, encargado o admin) y una sola parada.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-40 | El armado, la entrega, el colchón y la revisión de reclamos los registra el **personal de Yapa** (los administradores de `store.admins`). No se crea todavía un rol separado de armador o repartidor. | — |
| S-41 | Solo se arma un pedido **que se va a atender**: pago verificado, no cancelado por el cliente y con su grupo en el mínimo (LQ-01, LQ-02). Se arma **después del cierre** del ciclo. Un pedido puede tener varias bolsas; cada bolsa se registra con su foto (la referencia al archivo). | — |
| S-42 | La entrega se registra **por zona** (una parada) y es **todo o nada**: todos los pedidos atendidos de la zona deben tener al menos una bolsa armada. Se exige la foto de la entrega y el nombre de quien recibe, y se guarda la hora. Una zona se entrega una sola vez por ciclo. | — |
| S-43 | El plazo de reclamo es de **24 horas desde la hora de entrega de la zona**. Las 24 horas exactas ya están fuera (mismo criterio que S-02). | 24 h |
| S-44 | Un reclamo es por artículo: motivo `FALTANTE` o `DANADO`, foto obligatoria y cantidad mayor que 0 en el paso del producto. La suma de los reclamos no rechazados de un artículo no puede pasar de lo pedido. | — |
| S-45 | La revisión es caso por caso. Para **aprobar**, el ciclo tiene que estar liquidado, porque se necesita el precio final. Se abona como saldo el **precio final × cantidad**, redondeado al céntimo **hacia arriba** (a favor del cliente, S-09). Lo aprobado no puede pasar de lo entregado según la liquidación menos lo ya aprobado; así un faltante que ya se descontó en la liquidación no se devuelve dos veces. **Rechazar** no mueve dinero y esa cantidad se puede volver a reclamar dentro del plazo. | — |
| S-46 | El colchón solo guarda productos **no perecibles**: en el catálogo actual, la categoría `LIMPIEZA`. Su valor se calcula con el precio base del **primer tramo** del catálogo del ciclo (el más alto, así el tope nunca se subestima). El **tope es S/ 500** para todo el colchón. Al usar unidades, el valor baja en proporción. | S/ 500 |

## Reglas

### Armado

| Regla | Comportamiento | Error |
|---|---|---|
| AR-01 | Solo el personal de Yapa registra bolsas (S-40). | `NOT_AUTHORIZED` |
| AR-02 | El pedido existe. | `ORDER_NOT_FOUND` |
| AR-03 | El ciclo del pedido ya cerró (S-41). | `CYCLE_STILL_OPEN` |
| AR-04 | El pedido se va a atender (S-41). | `ORDER_NOT_ATTENDED` |
| AR-05 | Cada bolsa lleva una foto; las bolsas de un pedido se numeran 1, 2, 3... | `PHOTO_REQUIRED` |

### Entrega en portería

| Regla | Comportamiento | Error |
|---|---|---|
| EN-01 | Solo el personal de Yapa registra la entrega (S-40). | `NOT_AUTHORIZED` |
| EN-02 | La zona existe y no fue entregada en ese ciclo. | `ZONE_NOT_FOUND`, `ZONE_ALREADY_DELIVERED` |
| EN-03 | Foto de la entrega y nombre de quien recibe obligatorios. Se guardan con la hora y el tipo de recepción de la zona. | `PHOTO_REQUIRED`, `RECEIVER_REQUIRED` |
| EN-04 | La zona tiene pedidos atendidos en el ciclo. | `NOTHING_TO_DELIVER` |
| EN-05 | Todo o nada: todos los pedidos atendidos de la zona tienen al menos una bolsa (S-42). | `ORDERS_NOT_PACKED` |

### Reclamo por artículo

| Regla | Comportamiento | Error |
|---|---|---|
| RC-01 | Solo el dueño del pedido reclama. Para otro cliente el pedido "no existe" (como CE-01). | `ORDER_NOT_FOUND` |
| RC-02 | El pedido fue entregado. | `ORDER_NOT_DELIVERED` |
| RC-03 | Dentro de las 24 h desde la entrega (S-43). | `CLAIM_WINDOW_CLOSED` |
| RC-04 | Motivo `FALTANTE` o `DANADO`, con foto (S-44). | `INVALID_CLAIM_REASON`, `PHOTO_REQUIRED` |
| RC-05 | El artículo está en el pedido; la cantidad es un número mayor que 0 en el paso del producto, y con los otros reclamos no rechazados no pasa de lo pedido (S-44). | `INVALID_CLAIM_ITEM` |
| RC-06 | El reclamo queda `PENDIENTE` y no mueve dinero hasta que se revisa. | — |

### Revisión del reclamo

| Regla | Comportamiento | Error |
|---|---|---|
| RV-01 | Solo el personal de Yapa revisa (S-40). | `NOT_AUTHORIZED` |
| RV-02 | El reclamo existe y está `PENDIENTE`. | `CLAIM_NOT_FOUND`, `CLAIM_ALREADY_REVIEWED` |
| RV-03 | Para aprobar, el ciclo del pedido está liquidado (S-45). | `CYCLE_NOT_SETTLED` |
| RV-04 | Lo aprobado de un artículo no pasa de lo entregado según la liquidación (S-45). | `INVALID_CLAIM_ITEM` |
| RV-05 | Aprobado: se abona como saldo el precio final × cantidad, redondeado hacia arriba, y el reclamo queda `APROBADO`. Rechazado: queda `RECHAZADO` sin mover dinero (C-10, C-05, S-45). | — |

### Colchón de reposición

| Regla | Comportamiento | Error |
|---|---|---|
| CO-01 | Solo el personal de Yapa guarda o usa el colchón (S-40). | `NOT_AUTHORIZED` |
| CO-02 | El producto está en el catálogo del ciclo y no es perecible (S-46). | `PRODUCT_NOT_AVAILABLE`, `PERISHABLE_NOT_ALLOWED` |
| CO-03 | La cantidad es mayor que 0 y está en el paso del producto. | `INVALID_QUANTITY` |
| CO-04 | El valor total del colchón no pasa de S/ 500 (S-46). | `BUFFER_LIMIT_EXCEEDED` |
| CO-05 | Para reponer, se usa como máximo lo que hay guardado de ese producto; el valor baja en proporción. | `BUFFER_INSUFFICIENT`, `INVALID_QUANTITY` |

## Criterios de aceptación

Escenario: ciclo 2026-W38 con catálogo base. 8 pedidos verificados en la zona Z-JM-01, cada uno con la canasta de la iteración 2 (5 kg de papa amarilla + 10 kg de papa blanca + 10 kg de cebolla roja, pagado S/ 61.00). El ciclo cierra el miércoles 16/09 a las 20:00. Se arma el viernes 18/09 a las 10:00 y se entrega el sábado 19/09 a las 09:00 al "Sr. Ramos". En la liquidación, la cebolla queda en S/ 2.016 (tramo desde 80 kg).

- **AR-A · Armar.** Se registran dos bolsas con foto de un pedido → el pedido tiene las bolsas 1 y 2. → AR-05
- **AR-B · Bolsa sin foto.** Foto vacía o con solo espacios → `PHOTO_REQUIRED`. → AR-05
- **AR-C · Antes del cierre.** Armar el miércoles 16/09 a las 19:59 → `CYCLE_STILL_OPEN`. → AR-03
- **AR-D · Pedido que no se atiende.** Un pedido con pago sin verificar, un pedido cancelado por el cliente o un pedido de un grupo con solo 7 pedidos → `ORDER_NOT_ATTENDED`. Un pedido que no existe → `ORDER_NOT_FOUND`. → AR-02, AR-04
- **AR-E · Solo el personal.** Un vecino intenta registrar una bolsa → `NOT_AUTHORIZED`. → AR-01
- **EN-A · Entregar la zona.** Con los 8 pedidos armados, foto y "Sr. Ramos" → la entrega queda registrada con los 8 pedidos y la hora del sábado 09:00. → EN-03, EN-05
- **EN-B · Todo o nada.** Con 7 de los 8 pedidos armados → `ORDERS_NOT_PACKED`, y la zona sigue sin entrega. → EN-05
- **EN-C · Evidencia.** Sin foto → `PHOTO_REQUIRED`; sin quien recibe → `RECEIVER_REQUIRED`. → EN-03
- **EN-D · Una sola entrega.** Entregar la zona dos veces → `ZONE_ALREADY_DELIVERED`. → EN-02
- **EN-E · Zona sin pedidos o inexistente.** Z-LINCE-02 sin pedidos → `NOTHING_TO_DELIVER`; una zona que no existe → `ZONE_NOT_FOUND`; un vecino → `NOT_AUTHORIZED`. → EN-01, EN-02, EN-04
- **RC-A · Reclamar a tiempo.** El domingo 20/09 a las 08:59 el vecino reclama 1 kg de cebolla `DANADO` con foto → el reclamo queda `PENDIENTE` y su saldo no cambia. → RC-06
- **RC-B · Fuera de plazo.** El domingo 20/09 a las 09:00 → `CLAIM_WINDOW_CLOSED`. → RC-03
- **RC-C · Pedido no entregado o ajeno.** Reclamar antes de la entrega → `ORDER_NOT_DELIVERED`; otro vecino reclama sobre el pedido → `ORDER_NOT_FOUND`. → RC-01, RC-02
- **RC-D · Motivo y foto.** Motivo `OTRO` → `INVALID_CLAIM_REASON`; sin foto → `PHOTO_REQUIRED`. → RC-04
- **RC-E · Artículo inválido.** 0 kg, 1.5 kg, 11 kg o "abc" de cebolla, o limón (no está en el pedido) → `INVALID_CLAIM_ITEM`. Con 1 kg de cebolla ya reclamado, reclamar 10 kg más → `INVALID_CLAIM_ITEM`; 9 kg más → se acepta. → RC-05
- **RV-A · Aprobar.** Con el ciclo liquidado, se aprueba el reclamo de 1 kg de cebolla → el saldo del vecino sube S/ 2.02 (2.016 redondeado a su favor) y el reclamo queda `APROBADO`. → RV-05
- **RV-B · Rechazar.** Se rechaza el reclamo → queda `RECHAZADO`, el saldo no cambia, y el vecino todavía puede reclamar los 10 kg dentro del plazo. → RV-05, S-45
- **RV-C · Aprobar sin liquidar.** → `CYCLE_NOT_SETTLED`. → RV-03
- **RV-D · Revisión inválida.** Revisar dos veces → `CLAIM_ALREADY_REVIEWED`; un reclamo que no existe → `CLAIM_NOT_FOUND`; un vecino → `NOT_AUTHORIZED`. → RV-01, RV-02
- **RV-E · Sin doble devolución.** La liquidación ya descontó los 10 kg de cebolla del pedido como faltantes; aprobar un reclamo de 1 kg de cebolla → `INVALID_CLAIM_ITEM`. → RV-04
- **CO-A · Guardar.** 6 galones de limpiatodo → el colchón tiene 6 unidades con valor S/ 47.40 (6 × 7.90). → CO-02
- **CO-B · Tope.** 60 galones de limpiatodo (S/ 474.00) + 4 galones de lejía (S/ 26.00) = S/ 500.00 → se acepta. Un galón más de lejía → `BUFFER_LIMIT_EXCEEDED` y el valor sigue en S/ 500.00. → CO-04
- **CO-C · Producto no válido.** Papa amarilla → `PERISHABLE_NOT_ALLOWED`; un producto que no está en el catálogo → `PRODUCT_NOT_AVAILABLE`; 0 o 1.5 galones → `INVALID_QUANTITY`. → CO-02, CO-03
- **CO-D · Reponer.** De 6 galones guardados se usan 2 → quedan 4, con valor S/ 31.60. Usar 5 → `BUFFER_INSUFFICIENT`; usar un producto que no está guardado → `BUFFER_INSUFFICIENT`. → CO-05
- **CO-E · Solo el personal.** Un vecino intenta guardar o usar el colchón → `NOT_AUTHORIZED`. → CO-01

## Trazabilidad

| Regla | Código (`src/yapa_sdd/`) | Prueba (`tests/test_fulfillment.py`) |
|---|---|---|
| S-40 | `fulfillment.check_staff` (usado en armado, entrega, reclamos y colchón) | `test_ar_e_*`, `test_en_e_*`, `test_rv_d_*`, `test_co_e_*` |
| AR-01..AR-05, S-41 | `fulfillment.pack_bag`, `is_attended`, `check_photo`; `cycle.closes_at` | `test_ar_a_*`..`test_ar_e_*` |
| EN-01..EN-05, S-42 | `fulfillment.deliver_zone` | `test_en_a_*`..`test_en_e_*` |
| RC-01..RC-06, S-43, S-44 | `claims.file_claim`, `_claim_quantity` | `test_rc_a_*`..`test_rc_e_*` |
| RV-01..RV-05, S-45 | `claims.review_claim`; `settlement.settle_cycle` guarda `store.settlements[ciclo]` | `test_rv_a_*`..`test_rv_e_*` |
| CO-01..CO-05, S-46 | `buffer.add_to_buffer`, `use_buffer`, `buffer_value` | `test_co_a_*`..`test_co_e_*` |

## Huecos encontrados al implementar (a decidir por el equipo)

No se implementó nada para estos casos; se describe cómo se comporta hoy el código.

1. **Zona que no recibe.** Si la portería no está o no acepta las bolsas, no hay regla: la entrega simplemente no se registra y el pedido no puede reclamarse. Es el hueco H1.11 de `docs/analisis/03_huecos_negocio.md` (¿reintento?, ¿reembolso?).
2. **Liquidación antes de la entrega.** `settle_cycle` no exige que la zona esté entregada; la spec de la liquidación dice "después de la entrega", pero no hay una regla que lo obligue.
3. **Bolsas después de entregar.** Se pueden registrar bolsas de un pedido cuya zona ya se entregó.
4. **Uso del colchón.** Al reponer con el colchón no se registra a qué pedido fue; tampoco hay una regla que diga si ese faltante repuesto se descuenta del acuerdo con el proveedor (punto 5 del análisis).
5. **Devolución por reclamo al medio de pago.** Lo aprobado va a saldo (C-05); el cliente puede pedirlo de vuelta con BS-12, pero no se decidió si un artículo dañado debería devolverse directo a Yape o Plin.

## Fuera de alcance (con motivo)

- **Regla del 70 % para comprar la caja completa.** Es una recomendación del análisis, y el catálogo todavía no dice cuántas unidades trae cada caja.
- **Confirmación "recibí" del cliente.** El plazo de reclamo corre desde la entrega haya confirmación o no, así que no cambia ninguna regla de esta iteración.
- **Libro de Reclamaciones de Indecopi.** Es el reclamo legal formal; esta iteración cubre el reclamo operativo por artículo.

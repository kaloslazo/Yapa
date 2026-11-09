# Iteración 56 · Compra real con faltantes, dañados al armar, rotulado, bloqueo del despacho e incidencias de atención

## Requisito

Como Yapa, quiero registrar lo que de verdad llegó del proveedor y lo que se encontró dañado al armar, para que cada faltante se reponga con el colchón o vuelva al vecino en la liquidación sin que nadie tenga que reclamarlo. También quiero que cada bolsa lleve su rótulo, que una zona no salga a reparto antes de saber qué faltó, y que atención deje registro de lo que le cuentan los vecinos.

## Por qué

La iteración 55 dejó estas acciones del Informe PC3 (Tabla 3) para cuando el equipo decidiera cómo tocan el dinero. Kalos lo decidió el 09/11/2026:

- **Faltante del proveedor:** se repone primero con el colchón; lo que no alcance se descuenta a los últimos pedidos registrados y vuelve como saldo en la liquidación, al precio final. El tramo se sigue calculando con lo pedido.
- **Dañado al armar:** igual que un faltante. Yapa asume la pérdida y el vecino no tiene que reclamar.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-295 | **Compra real.** Compras (o el admin) registra, después del cierre, la cantidad que llegó de cada producto que se compra en el ciclo. Lo que no indica se considera recibido completo. Se registra **una sola vez** por ciclo. | una vez por ciclo |
| S-296 | **Reparto del faltante de compra.** Faltante = lo pedido entre los pedidos atendidos − lo recibido. Se descuenta a los pedidos con ese producto **empezando por el de número más alto** (el último registrado), cada uno hasta lo que pidió. En cada parte, si el producto es no perecible y hay colchón, se repone primero desde ahí (queda anotado como uso del colchón, S-122); el resto pasa a la liquidación como faltante (LQ-06) y se devuelve al precio final. El tramo se sigue decidiendo con lo pedido (LQ-03). | decisión del 09/11 |
| S-297 | **Dañado al armar.** El armador (o el admin) lo registra con foto, sobre un pedido que se atiende, con la compra ya registrada y antes de que la zona se entregue o falle. Se trata como el faltante de S-296: colchón primero y el resto como faltante en la liquidación. Lo descontado de un artículo (compra + dañados) no pasa de lo pedido. | decisión del 09/11 |
| S-298 | **Rotulado.** Cada bolsa tiene el rótulo "Pedido N · Zona · Bolsa n de T", donde T es el total de bolsas del pedido. La lista de armado lo trae listo para escribirlo o imprimirlo. | — |
| S-299 | **Bloqueo del despacho.** No se registra la entrega ni la entrega fallida de una zona hasta que el ciclo tenga su compra real registrada. Así, cuando sale el camión, ya se sabe qué faltó. | — |
| S-300 | **Incidencias de atención.** Atención (o el admin) registra una incidencia sobre un pedido, con un tipo (`ENTREGA`, `BOLSA`, `TRATO`, `OTRO`) y una descripción de 1 a 500 caracteres. Queda `ABIERTA` y se cierra con una nota. **No mueve dinero**: si corresponde devolver algo, va por reclamo (RC) o devolución (BS-12). | sin dinero |

Queda fuera "ver la app como un vecino desde atención": hoy solo lo tienen los admins de depuración (S-256) y abrirlo a atención es una decisión de privacidad.

## Reglas

### Compra real

| Regla | Comportamiento | Error |
|---|---|---|
| CR-01 | Solo compras o el admin registran la compra real. | `NOT_AUTHORIZED` |
| CR-02 | El ciclo ya cerró. | `CYCLE_STILL_OPEN` |
| CR-03 | Una sola vez por ciclo (S-295). | `PURCHASE_ALREADY_REGISTERED` |
| CR-04 | Cada producto indicado se compra en el ciclo (está en algún pedido atendido) y lo recibido es un número ≥ 0, en el paso del producto, y no mayor que lo pedido. | `INVALID_PURCHASE_ITEM` |
| CR-05 | El faltante se reparte según S-296. | — |
| CR-06 | `close_cycle` agrega al reporte de faltantes los de compra y de dañados que no cubrió el colchón. | `INVALID_MISSING_ITEM` (LQ-06) |

### Dañados al armar

| Regla | Comportamiento | Error |
|---|---|---|
| DA-01 | Solo el armador o el admin. | `NOT_AUTHORIZED` |
| DA-02 | El pedido existe, el ciclo cerró, el pedido se atiende y su zona no se entregó ni falló. | `ORDER_NOT_FOUND`, `CYCLE_STILL_OPEN`, `ORDER_NOT_ATTENDED`, `ZONE_ALREADY_CLOSED` |
| DA-03 | La compra real del ciclo ya está registrada (S-297). | `PURCHASE_NOT_REGISTERED` |
| DA-04 | Foto obligatoria. | `PHOTO_REQUIRED` |
| DA-05 | El artículo está en el pedido, la cantidad es mayor que 0 y está en el paso, y con lo ya descontado no pasa de lo pedido. | `INVALID_DAMAGED_ITEM` |
| DA-06 | Colchón primero; el resto es faltante en la liquidación (S-297). | — |

### Rotulado, despacho e incidencias

| Regla | Comportamiento | Error |
|---|---|---|
| RT-01 | La lista de armado trae el rótulo de cada bolsa (S-298). | — |
| BD-01 | La entrega y la entrega fallida exigen la compra real registrada (S-299). | `PURCHASE_NOT_REGISTERED` |
| IN-01 | Solo atención o el admin registran y cierran incidencias. | `NOT_AUTHORIZED` |
| IN-02 | El pedido existe; el tipo es válido; la descripción tiene de 1 a 500 caracteres. | `ORDER_NOT_FOUND`, `INVALID_INCIDENT` |
| IN-03 | Para cerrar: la incidencia existe, está abierta y la nota no va vacía. | `INCIDENT_NOT_FOUND`, `INCIDENT_ALREADY_CLOSED`, `INVALID_INCIDENT` |
| IN-04 | Una incidencia no mueve dinero (S-300). | — |

## Criterios de aceptación

Escenario base: el de las iteraciones 7 y 16 más 2 galones de limpiatodo. W38, Z-JM-01 (Residencial San Felipe) con 8 pedidos (1 a 8) de 5 kg de papa amarilla, 10 kg de papa blanca, 10 kg de cebolla roja y 2 galones de limpiatodo cada uno; todos verificados; se opera el viernes 18/09.

- **CR-A · Faltante de un fresco.** Llegan 36 kg de papa (se pidieron 40): el pedido 8 pierde 4 kg (pidió 5). En la liquidación el pedido 8 tiene 4 kg de papa faltante y le vuelve su valor al precio final; los pedidos 1 a 7 no cambian. El tramo de la papa sigue calculado con 40 kg. → CR-05, CR-06, S-296
- **CR-B · Faltante que pasa de un pedido.** Llegan 33 kg de papa: faltan 7 → el pedido 8 pierde 5 kg y el 7 pierde 2 kg. → S-296
- **CR-C · Colchón primero.** Con 3 galones de limpiatodo en el colchón, llegan 12 galones (faltan 4): el colchón cubre 2 del pedido 8 y 1 del pedido 7 (quedan 0 en el colchón) y el pedido 7 tiene 1 galón faltante en la liquidación. Los usos quedan anotados con su pedido. → S-296, S-122
- **CR-D · Datos.** Recibido mayor que lo pedido, negativo, 1.5 kg de papa, "abc" o un producto que nadie pidió → `INVALID_PURCHASE_ITEM`. Antes del cierre → `CYCLE_STILL_OPEN`. Un vecino o el armador → `NOT_AUTHORIZED`. Registrar dos veces → `PURCHASE_ALREADY_REGISTERED`. → CR-01..CR-04
- **CR-E · Sin faltantes.** Registrar la compra sin productos (todo llegó) no cambia la liquidación. → S-295
- **DA-A · Dañado.** Con la compra registrada, el armador marca 1 kg de cebolla dañada del pedido 3 con foto → en la liquidación el pedido 3 tiene 1 kg de cebolla faltante y le vuelve S/ 2,016 de ese kilo (antes del redondeo del total). → DA-05, DA-06
- **DA-B · Dañado repuesto con colchón.** Con 2 galones de limpiatodo en el colchón, el armador marca 1 galón dañado del pedido 3 → el colchón baja a 1 y el pedido 3 no tiene faltante. → DA-06
- **DA-C · Límites.** Cantidad 0, 1.5 kg, un producto que no está en el pedido o 10 kg de cebolla cuando ya hay 1 kg descontado → `INVALID_DAMAGED_ITEM`. Sin foto → `PHOTO_REQUIRED`. Sin compra registrada → `PURCHASE_NOT_REGISTERED`. Con la zona ya entregada → `ZONE_ALREADY_CLOSED`. Compras o atención → `NOT_AUTHORIZED`. → DA-01..DA-05
- **RT-A · Rótulo.** El pedido 1 con dos bolsas → rótulos "Pedido 1 · Residencial San Felipe · Bolsa 1 de 2" y "Pedido 1 · Residencial San Felipe · Bolsa 2 de 2" (el nombre es el de la zona). → RT-01
- **BD-A · Bloqueo.** Con todo armado y sin compra registrada, entregar Z-JM-01 o registrar su falla → `PURCHASE_NOT_REGISTERED`. Después de registrar la compra, se entrega. → BD-01
- **IN-A · Incidencia.** Atención registra `ENTREGA` "La portería dice que llegó tarde" sobre el pedido 2 → queda `ABIERTA`; la cierra con "Se habló con el vecino" → `CERRADA`. El saldo y la conciliación no cambian. → IN-02..IN-04
- **IN-B · Datos.** Tipo `QUEJA`, descripción vacía o de 501 caracteres → `INVALID_INCIDENT`; pedido 999 → `ORDER_NOT_FOUND`; cerrar dos veces → `INCIDENT_ALREADY_CLOSED`; cerrar sin nota → `INVALID_INCIDENT`; una incidencia que no existe → `INCIDENT_NOT_FOUND`; el armador → `NOT_AUTHORIZED`. → IN-01..IN-03
- **API-A · Rutas.** `POST /api/compras/recibido`, `POST /api/admin/danados`, `GET /api/admin/incidencias`, `POST /api/admin/incidencias` y `POST /api/admin/incidencias/{id}/cerrar` responden según los roles de CR-01, DA-01 e IN-01. `GET /api/compras` dice si la compra está registrada y lista los faltantes; `GET /api/admin/armado` trae los rótulos. → todas

## Cambios en pruebas anteriores (por S-299)

Las pruebas que entregan o registran una falla agregan, **en su preparación**, "compras registra la compra completa" antes de despachar (ayudante `buy_all` de `test_settlement.py`, o `POST /api/compras/recibido` en las de la API). No cambia ningún número que verifican. Archivos: `test_fulfillment`, `test_failed_delivery`, `test_failed_zone_metrics`, `test_gaps_packing`, `test_metrics`, `test_personal_por_rol`, `test_proveedores_transportistas`, `test_web_operacion`, `test_web_hardening`, `test_api`, `test_avisos` y `test_e2e_week`. El bloqueo se revisa **al final** de la entrega (después de EN-01..EN-05 y EF-01..EF-02), así que los errores que ya verificaban esas pruebas no cambian. La semana de demostración (`demo.py`) también registra la compra.

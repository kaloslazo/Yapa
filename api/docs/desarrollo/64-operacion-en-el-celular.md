# Iteración 64 · La operación en el celular

## Requisito

Como persona del equipo (armado, compras, atención, portería, reparto o proveedor), quiero hacer mi trabajo desde el celular sin pelear con tablas que se cortan, sin escribir códigos de memoria y viendo nombres y fotos en lugar de claves internas. El armador, sobre todo, trabaja con las manos ocupadas: necesita ver qué va en cada bolsa y tomarle la foto con un toque.

## Por qué

En la demo del 12/11/2026 el profesor recomendó especializar las pantallas de operación para el celular. La revisión pantalla por pantalla, en un celular de 390 px, encontró:

- Todas las tablas del panel (Armado, Reclamos, Devoluciones, Compras, Resumen, Cuentas) se salen por la derecha: las acciones quedan fuera de la pantalla.
- Hay que **escribir códigos** para guardar en el colchón (`LIMPIATODO-GALON`), reponer un faltante (pedido y código) y registrar una incidencia (número de pedido).
- Se ven **claves internas** en lugar de palabras: `Z-LINCE-01`, `SUP-FRESCOS`, `G-LINCE`, `LIMON`, `SOLICITUD_CLIENTE`, `Semana 2026-W40`.
- El armado es una tabla de texto pequeño; el botón de la foto está en la última columna, fuera de la pantalla.

## Alcance

Es una iteración de pantallas. **No cambia ninguna regla de negocio ni mueve dinero**: el motor solo agrega datos de lectura (nombres) y una consulta para elegir pedidos.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-327 | En pantallas de hasta 720 px de ancho, cada fila de una tabla del panel se muestra como una tarjeta, con el nombre de la columna junto a cada dato. En computadora, las tablas siguen como están. | 720 px |
| S-328 | **Nombres en lugar de claves.** El panel muestra la zona por su nombre, la semana por sus fechas ("28 sep – 4 oct 2026"), el proveedor por su nombre, el producto por su nombre y su foto, y el motivo de una devolución en palabras ("Pidió su saldo"). Las claves solo quedan donde el equipo las necesita para hablar con otro sistema (el código YP del pago). | — |
| S-329 | **Elegir en vez de escribir.** Guardar en el colchón se hace eligiendo un producto de limpieza del catálogo de la semana; reponer un faltante se hace desde la fila del faltante, eligiendo solo la cantidad; una incidencia se registra eligiendo el pedido de una lista que se puede buscar por número, vecino o edificio. | — |
| S-330 | Para la lista de pedidos de atención, el motor da `GET /api/admin/pedidos?ciclo=` a atención y al admin: número, vecino, edificio y estado de cada pedido de la semana, **sin montos ni productos** (atención no los necesita para registrar una incidencia). | sin montos |
| S-331 | **Armado en el celular.** Cada pedido es una tarjeta con el vecino, el edificio, el rótulo y la lista de productos con su foto y cantidad. El armador puede marcar cada producto al meterlo en la bolsa (es una ayuda en pantalla: no se guarda). El botón grande **Tomar foto de la bolsa** abre la cámara y la bolsa se registra apenas se elige la foto. Arriba, una barra dice cuántos pedidos ya tienen bolsa. | marcas sin guardar |
| S-332 | La portería ve el nombre de su edificio, sin la clave de la zona. El reparto registra la entrega con un botón grande de cámara. El proveedor ve la clave de un producto solo al crear uno nuevo. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| OC-01 | `GET /api/admin/pedidos` responde a atención y al admin; a cualquier otro rol, 403. | `FORBIDDEN` |
| OC-02 | Trae `ciclo`, `ciclos` y `pedidos` con `id`, `vecino`, `zona` (nombre del edificio) y `estado`. No trae montos, productos ni datos de contacto (S-330). | — |
| OC-03 | Los reclamos del panel traen `nombre` del producto; los faltantes de la compra y el colchón también traen `nombre`. | — |
| OC-04 | La compra de la semana trae `guardables`: los productos de limpieza del catálogo de la semana (id, nombre y unidad), para elegir qué guardar en el colchón (S-329). | — |
| OC-05 | Los pedidos del panel traen `zona_nombre`. | — |

## Criterios de aceptación

Escenario base: la semana de demo (2026-W40) cerrada, con la compra registrada.

- **OC-A · Pedidos para atención.** Atención pide `GET /api/admin/pedidos?ciclo=2026-W40` y recibe los 8 pedidos de Los Álamos con vecino, edificio "Edificio Los Álamos" y estado; ninguno trae `total`, `lineas` ni `celular`. El armador recibe 403. → OC-01, OC-02
- **OC-B · Nombres.** Un reclamo de 1 kg de limón trae `nombre` "Limón"; un faltante de papa amarilla trae `nombre` "Papa amarilla"; el colchón con 2 galones de limpiatodo trae su nombre. → OC-03
- **OC-C · Guardables.** La compra de la semana trae entre sus `guardables` el limpiatodo y el detergente, y ningún producto fresco. → OC-04
- **OC-D · Zona por nombre.** Los pedidos del resumen y del armado traen `zona_nombre` "Edificio Los Álamos". → OC-05
- **OC-E · Tablas en el celular.** En el panel, cada celda de una tabla lleva el nombre de su columna para mostrarse como tarjeta en el celular. → S-327
- **OC-F · Sin escribir códigos.** El colchón se llena eligiendo el producto de una lista con su nombre; la incidencia se registra eligiendo el pedido de una lista. Ninguno de los dos formularios tiene un campo de texto para un código. → S-329
- **OC-G · Armado.** El armador ve una tarjeta por pedido con sus productos, la barra "N de M pedidos con bolsa" y un botón de cámara por pedido; al elegir la foto, se registra la bolsa sin otro toque. → S-331
- **OC-H · Sin claves a la vista.** En Armado, Atención, Compras, Portería y Resumen no aparecen `Z-LINCE-01`, `SUP-FRESCOS` ni `SOLICITUD_CLIENTE`. → S-328, S-332

## Cambios en pruebas anteriores

- `test_compra_real.test_api_a_purchase_damaged_labels_and_incidents` compara el faltante campo por campo: ahora espera también `nombre` "Papa amarilla" (OC-03). La comparación sigue siendo exacta.
- `operations.test.ts` (PA-02, iteración 63): el filtro por zona se comprueba sobre las tarjetas de armado (`.pack-card`) en lugar de las filas de la tabla, porque el armado ya no es una tabla (S-331).

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| OC-01, OC-02, S-330 | `web/api.py` `admin_pedidos` (ruta con `ATTENDING`) | `test_operacion_celular_64.test_oc_a_*` |
| OC-03 | `claim_json`, `shortage_json` y `admin_colchon` con `nombre` | `test_oc_b_*`, `test_compra_real.test_api_a_*` |
| OC-04, S-329 | `compras` con `guardables` (categorías de `buffer.NON_PERISHABLE`) | `test_oc_c_*` |
| OC-05 | `order_json` con `zona_nombre`; `PACKER_ORDER` lo incluye | `test_oc_d_*` |
| S-327 | `labelTables` en `AdminPanel.tsx` (pone `data-label` a cada celda) y la regla `@media (max-width: 720px)` de `styles.css` | `operacionCelular.test.ts` OC-E |
| S-328 | `CycleSelect` con fechas, `REASONS` y `AI_CATEGORIES` en palabras, `ProductThumb.tsx`, zona y proveedor por nombre | OC-H |
| S-329 | `Purchases` (colchón con `guardables`, reponer desde el faltante) e `Incidents` (pedido elegido de `/api/admin/pedidos`, con búsqueda) | OC-F |
| S-331 | `Packing` y `PackCard` en `AdminPanel.tsx` (marcas en pantalla, cámara que sube al elegir la foto) | OC-G |
| S-332 | `PartnerPanel.tsx` (edificio por nombre, foto de producto, `PhotoForm` grande para el reparto) y `SupplierListEditor.tsx` (clave solo para un producto nuevo) | OC-H |

## Evidencia

- `64-motor-rojo.txt` y `64-web-rojo.txt`: las pruebas nuevas fallan antes del código (6 del motor y 6 de la web).
- `64-motor-verde.txt`: 731 pruebas del motor en verde.
- `64-web-verde.txt`: TypeScript, 176 pruebas de la web y build en verde.
- Revisión en un celular de 390 px con la demo local (12/11/2026): Armado, Compras, Reclamos, Incidencias, Devoluciones y Portería sin tablas cortadas ni claves internas; el selector de semana ya no deja un hueco de 200 px en la caja de arriba.
- Segunda revisión (12/11/2026, noche): en el celular los textos largos de una tarjeta se cortan en varias líneas (los tramos del catálogo se montaban sobre su etiqueta); la foto del producto en el editor del proveedor ya no se estira; "Lista lista para revisar" pasa a "Sin cambios por enviar"; en Métricas la semana sin liquidar se nombra por sus fechas. Recorrido real en Chrome de compras, armado, reclamo del vecino, atención, portería, reparto y admin: 23 de 23 comprobaciones en verde.

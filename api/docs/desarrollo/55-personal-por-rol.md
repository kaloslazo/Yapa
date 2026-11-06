# Iteración 55 · Cuentas para compras, armado, atención y portería

## Requisito

- Como **encargado de compras**, quiero ver en una sola pantalla cuánto hay que comprarle a cada proveedor esta semana y manejar el colchón, sin pedirle al administrador que me pase los números.
- Como **armador**, quiero ver los pedidos por armar y registrar cada bolsa con su foto desde mi cuenta.
- Como **atención al cliente**, quiero resolver los reclamos, pagar las devoluciones y atender los pedidos de PIN sin tener acceso a la caja ni al catálogo.
- Como **portería** del edificio (o como **admin de zona** cuando la zona recibe por mí), quiero ver qué bolsas llegaron y de qué vecino son, y confirmar que las recibí para que cada vecino sepa que ya puede bajar a buscarlas.
- Como **administrador**, quiero crear y desactivar estas cuentas igual que las de reparto y proveedor.

## Por qué

El Informe PC3 (Tabla 3, mapa de roles) define 10 roles con su cuenta y su panel, pero la web solo tenía cinco: vecino, admin de zona, administrador, transportista y proveedor. Hasta hoy el administrador hacía el trabajo de compras, armado y atención (S-40), y nadie confirmaba la recepción en el edificio. El 06/11 el equipo anotó que "nos faltan varios roles". Esta iteración reparte permisos sobre lo que el motor ya hace. Las acciones nuevas del informe (compra real con faltantes, rotulado, dañados, bloqueo del despacho, incidencias, ver la app como vecino) quedan para la iteración 56.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-289 | **Las cuentas de compras, armado, atención y portería las crea el administrador**, con las mismas reglas que las de la iteración 54: usuario S-279, contraseña de 10 caracteres o más, bloqueo por intentos, desactivar borra la contraseña (S-278..S-280). Todas llevan nombre. | solo el admin |
| S-290 | El **armador** ve la lista de armado y registra bolsas con las reglas de siempre (AR de la iteración 15, como el administrador). No verifica pagos, no ve saldos, reclamos ni devoluciones. | solo arma |
| S-291 | **Compras** ve, por cada proveedor aliado, sus productos del ciclo con la cantidad, el tramo alcanzado, el precio y el monto (el mismo cálculo de S-288), y el colchón con su tope. Agrega y usa colchón con las reglas CO-01..CO-08. No verifica pagos, no ve saldos, no liquida ni publica el catálogo. | compra y colchón |
| S-292 | **Atención** revisa reclamos (RV), marca devoluciones pagadas (BS-13) y atiende los pedidos de PIN: los descarta o le genera al vecino un PIN nuevo (OP-08). No publica el catálogo, no verifica pagos ni liquida. | reclamos, devoluciones y PIN |
| S-293 | Cada cuenta de **portería** pertenece a **una zona**. Ve las entregas de su zona en el ciclo y, por pedido, solo el número, el nombre del vecino (para saber a quién darle la bolsa) y cuántas bolsas lleva. **No ve productos, montos ni celulares.** | su zona, sin montos |
| S-294 | **Quien recibe en la zona confirma la recepción** de una entrega ya registrada: la portería de esa zona o su admin de zona, este último desde su panel y sin cuenta nueva. Se confirma una sola vez. Cada vecino de la entrega recibe el aviso "Tus bolsas ya están en el edificio". La confirmación no mueve dinero ni cambia el plazo de reclamo (S-43). | portería o admin de zona |

## Reglas

### Cuentas

| Regla | Comportamiento | Error |
|---|---|---|
| CX-07 | Solo un administrador crea cuentas de compras, armado, atención o portería, con las reglas CX-02 y CX-03 (usuario, nombre y contraseña). | `NOT_AUTHORIZED`, `INVALID_USER`, `USER_TAKEN`, `NAME_REQUIRED`, `INVALID_PASSWORD` |
| CX-08 | La cuenta de portería apunta a una zona que existe (S-293). | `ZONE_NOT_FOUND` |
| CX-09 | Cada tipo de cuenta usa solo sus rutas (CX-06). Las rutas de armado, reclamos, devoluciones y pedidos de PIN las comparten el administrador y el rol que las atiende. | 403 `FORBIDDEN` |

### Armado

| Regla | Comportamiento | Error |
|---|---|---|
| AM-01 | El armador ve la lista de armado (pedido, vecino, productos y bolsas, **sin montos ni datos de pago**) y registra bolsas con las mismas reglas que el administrador. | los de armado |
| AM-02 | Un armador desactivado, o una cuenta que no es armador ni administrador, no registra bolsas. | `NOT_AUTHORIZED` |

### Compras

| Regla | Comportamiento | Error |
|---|---|---|
| CP-01 | `GET /api/compras?ciclo=` da la compra del ciclo por proveedor (S-291) y el colchón. | |
| CP-02 | Compras agrega al colchón con las reglas CO-02..CO-04. | `PRODUCT_NOT_AVAILABLE`, `PERISHABLE_NOT_ALLOWED`, `INVALID_QUANTITY`, `BUFFER_LIMIT_EXCEEDED` |
| CP-03 | Compras repone el faltante de un pedido desde el colchón con las reglas CO-05..CO-08. | `BUFFER_INSUFFICIENT`, `BUFFER_NOT_FOR_ORDER`, … |
| CP-04 | Solo el administrador o compras tocan el colchón. | `NOT_AUTHORIZED` |

### Atención

| Regla | Comportamiento | Error |
|---|---|---|
| AT-01 | Atención revisa reclamos con las reglas RV (aprobar abona saldo). | los de RV |
| AT-02 | Atención marca una devolución como pagada con su código de operación (BS-13). | `REFUND_NOT_FOUND`, `REFUND_ALREADY_PAID` |
| AT-03 | Atención descarta un pedido de PIN o le genera un PIN nuevo al vecino. | `PIN_REQUEST_NOT_FOUND` |
| AT-04 | Solo el administrador o atención revisan reclamos y atienden pedidos de PIN. | `NOT_AUTHORIZED` |

### Recepción en el edificio

| Regla | Comportamiento | Error |
|---|---|---|
| PO-01 | La portería ve las entregas de su zona en el ciclo con su estado (`pendiente`, `entregada`, `fallida` o `recibida`) y lo que dice S-293. | |
| PO-02 | Confirman la recepción la portería de la zona o su admin de zona. Una portería de otra zona o un vecino que no administra esa zona no puede. Otro tipo de cuenta tampoco. | `FOREIGN_ZONE`, `NOT_AUTHORIZED` |
| PO-03 | Solo se confirma una entrega registrada (no pendiente ni fallida). | `DELIVERY_NOT_FOUND` |
| PO-04 | Se confirma una sola vez; cada vecino de la entrega recibe el aviso (S-294). | `ALREADY_CONFIRMED` |

## Criterios de aceptación

Base: datos del piloto, ciclo 2026-W38 con 8 pedidos verificados en Z-JM-01 (5 kg de papa amarilla, 10 kg de papa blanca y 10 kg de cebolla roja cada uno), igual que la iteración 54.

| # | Criterio | Resultado |
|---|---|---|
| CX-J | El admin crea `compras-1`, `armado-1`, `atencion-1` y `porteria-jm` (zona Z-JM-01); cada una entra con su tipo y `rol` igual al tipo | 201, luego 200 |
| CX-K | Un armador intenta crear una cuenta | `NOT_AUTHORIZED` en el motor, 403 en la API |
| CX-L | Portería para la zona `Z-NO-EXISTE` | `ZONE_NOT_FOUND` |
| CX-M | Cuenta de armado sin nombre; usuario `armado-1` repetido | `NAME_REQUIRED`, `USER_TAKEN` |
| CX-N | El armador pide `/api/admin/reclamos`, `/api/admin/pedidos/1/verificar`, `/api/compras`; atención pide `/api/admin/catalogo`, `/api/admin/armado`; compras pide `/api/admin/devoluciones`, `/api/admin/conciliacion`; portería pide `/api/admin/armado`, `/api/reparto`; el transportista pide `/api/porteria` | 403 |
| AM-A | El armador ve los 8 pedidos de Z-JM-01 por armar, sin `total`, `pago` ni `codigo_pago`, y registra la bolsa del primero con foto: queda con `packed_by = armado-1` | bolsa 1 |
| AM-B | Un armador desactivado arma desde el motor; un transportista arma | `NOT_AUTHORIZED` |
| CP-A | Con W38 cerrado, compras ve a `SUP-FRESCOS` con papa amarilla 40 kg, papa blanca 80 kg y cebolla roja 80 kg, cada una con tramo, precio y monto, y el total del proveedor; ve el colchón en S/ 0 con tope S/ 500 | por proveedor |
| CP-B | Compras agrega 2 unidades de `LIMPIATODO-GALON` al colchón (limpieza, S-46) | colchón con 2 |
| CP-C | Compras agrega papa amarilla (perecible) | `PERISHABLE_NOT_ALLOWED` |
| CP-D | Un armador agrega al colchón | `NOT_AUTHORIZED` |
| CP-E | Compras abre W40 antes de su cierre, sin pedidos: la respuesta dice `parcial: true` aunque no haya proveedores (hallazgo al probar en la demo) | parcial |
| AT-A | Con W38 liquidado y entregado, un vecino reclama 1 kg de cebolla faltante; atención lo aprueba y el vecino recibe el saldo | aprobado |
| AT-B | Un armador revisa un reclamo | `NOT_AUTHORIZED` |
| AT-C | Atención descarta un pedido de PIN y genera un PIN nuevo para el vecino 101 | descartado; PIN de 6 dígitos |
| PO-A | Con la entrega de Z-JM-01 registrada, `porteria-jm` ve 1 entrega `entregada` con 8 pedidos, cada uno con el nombre del vecino y 1 bolsa; la respuesta no trae montos, productos ni celulares | 1 entrega |
| PO-B | `porteria-jm` confirma: la entrega pasa a `recibida` con `received_by = porteria-jm` y cada uno de los 8 vecinos tiene el aviso "Tus bolsas ya están en el edificio" | recibida, 8 avisos |
| PO-C | Confirmar otra vez | `ALREADY_CONFIRMED` |
| PO-D | Confirmar antes de que el transportista entregue | `DELIVERY_NOT_FOUND` |
| PO-E | Una portería de Z-LINCE-01 confirma Z-JM-01 | `FOREIGN_ZONE` |
| PO-F | El vecino 1001, admin de Z-JM-01, confirma desde `POST /api/zona/recepciones`; otro vecino de la zona que no es admin recibe `FOREIGN_ZONE` | recibida |
| PO-G | Un armador intenta confirmar desde el motor | `NOT_AUTHORIZED` |

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| CX-07 | `partners.create_staff` (S-289), reutiliza `_check_admin`, `_check_user` y `_check_password` | `test_cx_j_admin_creates_the_four_staff_accounts`, `test_cx_k_only_admin_creates_staff_accounts`, `test_cx_m_name_and_unique_user`, `test_cx_unknown_staff_kind_is_rejected`, `test_cx_j_api_creates_staff_accounts`, `test_cx_k_packer_cannot_create_accounts` |
| CX-08 | `partners.create_staff` con `zone_id` (S-293) | `test_cx_l_concierge_needs_existing_zone` |
| CX-09 | `web/api.py`: `KINDS` suma los cuatro tipos; una ruta declara un rol o una tupla de roles (`PACKING`, `BUYING`, `ATTENDING`, `PHOTO_VIEWERS`) y `dispatch` responde 403 si la sesión no está | `test_cx_n_each_role_only_uses_its_routes` |
| AM-01 | `fulfillment.pack_bag` usa `check_role(..., PACKER)`; `admin_armado` quita montos y pagos para el armador (`PACKER_ORDER`) | `test_am_a_packer_packs_a_bag`, `test_am_a_packer_list_has_no_money` |
| AM-02 | `fulfillment.check_role` con `partners.can` | `test_am_b_deactivated_packer_and_driver_cannot_pack` |
| CP-01 | `web/api.py` `compras` (usa `supplier_offers.supplier_order` por proveedor aliado y `admin_colchon`) | `test_cp_a_buyer_sees_purchase_by_supplier`, `test_cp_e_open_cycle_is_partial_even_without_suppliers` |
| CP-02, CP-03 | `buffer.add_to_buffer` y `use_buffer` con `check_role(..., BUYER)`; rutas `/api/compras/colchon*` | `test_cp_b_buyer_adds_to_buffer`, `test_cp_c_buyer_follows_buffer_rules`, `test_cp_b_buyer_adds_and_uses_buffer_from_api` |
| CP-04 | `check_role(..., BUYER)` | `test_cp_d_packer_does_not_touch_buffer` |
| AT-01 | `claims.review_claim` con `check_role(..., SUPPORT)` | `test_at_a_support_approves_claim` |
| AT-02 | ruta `/api/admin/devoluciones*` abierta a `ATTENDING` | `test_cx_n_each_role_only_uses_its_routes` |
| AT-03 | `customers._check_support` en `dismiss_pin_request` y `reset_pin` | `test_at_c_support_handles_pin_requests`, `test_at_c_support_resets_pin_from_api` |
| AT-04 | `check_role(..., SUPPORT)` y `customers._check_support` | `test_at_b_packer_does_not_review_claims`, `test_at_c_support_handles_pin_requests` |
| PO-01 | `reception.for_zone`; rutas `/api/porteria` y `/api/zona/recepcion` | `test_po_a_concierge_sees_its_zone_without_money`, `test_po_concierge_flow_from_api` |
| PO-02 | `reception._check_receiver` | `test_po_e_concierge_of_other_zone`, `test_po_f_zone_admin_confirms_other_neighbor_cannot`, `test_po_g_other_accounts_cannot_confirm`, `test_po_deactivated_concierge_cannot_confirm`, `test_po_f_zone_admin_confirms_from_api` |
| PO-03 | `reception.confirm_reception` | `test_po_d_needs_a_registered_delivery` |
| PO-04 | `reception.confirm_reception` guarda en `store.receptions`; la API manda `notices.in_building` con `tell` (AV-11) | `test_po_b_concierge_confirms_and_neighbors_are_told`, `test_po_c_confirms_only_once` |

Web:
- El acceso del equipo cambia el selector de tres opciones por una grilla con ícono: Administración, Compras, Armado, Atención, Portería, Reparto y Proveedor (`AuthDialog.tsx`).
- Compras, armado y atención entran al mismo panel del equipo, pero cada uno ve solo sus secciones (`utils/adminSections.ts`, `AdminPanel.tsx`) y no tiene tienda:
  - compras ve "Compra de la semana": el total por proveedor, el colchón y los formularios para guardar y reponer;
  - el armador ve el armado sin las acciones de entrega;
  - atención ve reclamos, devoluciones y "Pedidos de PIN".
- La portería tiene su pantalla para el celular (`PartnerPanel.tsx`, `ReceptionCard.tsx`).
- El admin de zona ve la misma tarjeta en su panel (`ZonePage.tsx`) cuando hay algo que entregar.
- La sección del admin "Proveedores y reparto" pasa a llamarse "Cuentas del equipo" y crea los seis tipos de cuenta; la portería pide su zona.
- La demo local crea `compras-demo`, `armado-demo`, `atencion-demo` y `porteria-demo` (Z-LINCE-01) en `web/__main__.py`.

Hallazgos al probar:
- **Lista de armado.** `admin_armado` devolvía los montos y el código de pago de cada pedido. Para el armador se recortan (S-290) y la spec se actualizó antes del código (AM-01).
- **Avisos.** La confirmación del motor no manda avisos: lo hace la API con `tell`, como en la entrega (AV-11). La prueba PO-B del motor llama a `notices.in_building` y la de la API comprueba el aviso.
- **Ciclo abierto.** En la demo, con W40 abierta y sin pedidos, la pantalla de compras decía "Cerrado", porque el estado salía de los proveedores. La API ahora da `parcial` del ciclo (CP-E).
- **`check_staff`.** `fulfillment.check_staff` quedó sin uso y se quitó.

Evidencia: `docs/evidencia/desarrollo/55-personal-por-rol-rojo.txt` (el módulo `reception` no existía) y `55-personal-por-rol-verde.txt`.


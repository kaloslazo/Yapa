# Iteración 54 · Cuentas para proveedores y transportistas

## Requisito

- Como **transportista**, quiero ver en mi celular las paradas del sábado con las bolsas de cada una, y registrar ahí mismo la entrega (o por qué no se pudo) con la foto, sin depender de que alguien del equipo lo cargue después.
- Como **proveedor aliado**, quiero mandar mi lista de la semana (tramos y máximo) desde la web y ver cuánto me compra Yapa de cada producto, sin pasar la lista por WhatsApp.
- Como **administrador**, quiero crear y desactivar esas cuentas, y seguir siendo el único que publica el catálogo.

## Por qué

El 26/10 el equipo anotó que falta pulir "la interfaz de proveedores y transportistas". Hasta ahora solo existen dos tipos de cuenta: vecino y equipo (S-40: el personal son los administradores). El transportista no podía registrar la entrega y el proveedor mandaba su lista para que el administrador la pegara (S-116).

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-278 | **Las cuentas de proveedor y transportista las crea el administrador**; nadie se registra solo. Entran con usuario y contraseña, como el equipo (mínimo 10 caracteres, S-70), con el mismo bloqueo por intentos (S-68). | solo el admin las crea |
| S-279 | El usuario tiene de 3 a 30 caracteres: minúsculas, números y guiones. Es único entre administradores, proveedores y transportistas. | `[a-z0-9-]{3,30}` |
| S-280 | Desactivar una cuenta borra su contraseña: no puede entrar y sus sesiones abiertas se cierran en el siguiente pedido (SG-05). Para reactivarla, el administrador le pone una contraseña nueva. Lo que ya registró se conserva. | se conserva |
| S-281 | El transportista **solo entrega**: registra la entrega o la falla de una zona con las mismas reglas que el equipo (EN-01..EN-05, EF-01..EF-03). No arma bolsas, no verifica pagos ni ve el panel. | solo entrega |
| S-282 | El transportista ve de cada parada: nombre de la zona, distrito, quién recibe, el contacto de la recepción, la ubicación, y por pedido solo el número y cuántas bolsas lleva. **No ve nombres de vecinos, celulares ni montos.** | sin datos de vecinos |
| S-283 | Cada cuenta de proveedor pertenece a **un proveedor aliado**. Si el administrador da un código de proveedor que no existe y un nombre, se registra como proveedor aliado nuevo. Un proveedor que no es aliado no puede tener cuenta. | un proveedor por cuenta |
| S-284 | El proveedor **propone** su lista para un ciclo que todavía no abre, en el mismo formato que pega el administrador (S-116). La propuesta no cambia el catálogo: queda pendiente hasta que el administrador la aprueba (RN-16). Puede reenviarla mientras no abra el ciclo; la nueva reemplaza a la anterior y vuelve a quedar pendiente. | propone, no publica |
| S-285 | La columna `proveedor` de su lista puede ir vacía o con su propio código; con otro código se rechaza. Un código de producto que en el catálogo del ciclo es de otro proveedor también se rechaza. | solo lo suyo |
| S-286 | Al aprobar, en el catálogo del ciclo **los productos de ese proveedor se reemplazan por los de su lista** (lo que no mandó deja de estar ese ciclo). Los de los demás proveedores no cambian. Se valida igual que una publicación del administrador (CT-02..CT-08) y es todo o nada. | reemplaza solo lo suyo |
| S-287 | Para rechazar una propuesta el administrador escribe el motivo, y el proveedor lo ve. | motivo obligatorio |
| S-288 | El proveedor ve, de **sus** productos en el ciclo, la cantidad total de los pedidos que se atienden (el mismo criterio de la liquidación, S-41), el tramo alcanzado, su precio de ese tramo (sin la comisión de Yapa) y el monto. Antes del cierre del miércoles el número es parcial y se marca así. No ve vecinos ni pedidos sueltos. | totales, sin vecinos |

## Reglas

### Cuentas

| Regla | Comportamiento | Error |
|---|---|---|
| CX-01 | Solo un administrador crea, desactiva o cambia la contraseña de una cuenta de proveedor o transportista. | `NOT_AUTHORIZED` |
| CX-02 | El usuario cumple S-279 y no está usado. | `INVALID_USER`, `USER_TAKEN` |
| CX-03 | El nombre no va vacío (transportista). La contraseña tiene al menos 10 caracteres. | `NAME_REQUIRED`, `INVALID_PASSWORD` |
| CX-04 | La cuenta de proveedor apunta a un proveedor aliado (S-283). | `SUPPLIER_NOT_ALLIED`, `SUPPLIER_NOT_FOUND` |
| CX-05 | Una cuenta desactivada no entra; sus sesiones se cierran (S-280). | `INVALID_CREDENTIALS` |
| CX-06 | Cada tipo de cuenta solo usa sus rutas: un proveedor o transportista no entra a las del vecino ni a las del equipo, y viceversa. | 403 `FORBIDDEN` |

### Transportista

| Regla | Comportamiento | Error |
|---|---|---|
| TR-01 | `GET /api/reparto?ciclo=` lista las paradas del ciclo (zonas con pedidos atendidos) con lo que dice S-282 y el estado de cada una: pendiente, entregada o fallida. | |
| TR-02 | Registra la entrega de una zona (foto y quién recibe) con las reglas EN-01..EN-05; queda `delivered_by` con su usuario y el vecino recibe el aviso de siempre. | los de EN |
| TR-03 | Registra la entrega fallida (foto y motivo) con las reglas EF-01..EF-03. | los de EF |
| TR-04 | No arma bolsas (S-281). | `NOT_AUTHORIZED` |

### Proveedor

| Regla | Comportamiento | Error |
|---|---|---|
| PV-01 | Manda su lista para un ciclo que no abrió (S-284). | `CATALOG_LOCKED`, `INVALID_CATALOG_FORMAT` |
| PV-02 | Cada producto pasa las mismas validaciones del catálogo (tramos, máximo, unidad, categoría, duplicados). | `INVALID_TIERS`, `INVALID_STOCK`, `INVALID_UNIT`, `INVALID_CATEGORY`, `DUPLICATE_PRODUCT` |
| PV-03 | Solo sus productos (S-285). | `FOREIGN_SUPPLIER`, `FOREIGN_PRODUCT` |
| PV-04 | El administrador aprueba una propuesta pendiente: se publica según S-286. | `OFFER_NOT_FOUND`, `OFFER_NOT_PENDING`, los de CT |
| PV-05 | El administrador la rechaza con motivo (S-287). | `REASON_REQUIRED`, `OFFER_NOT_PENDING` |
| PV-06 | El proveedor ve el estado de sus propuestas y su pedido consolidado del ciclo (S-288). | |

## Criterios de aceptación

Base: datos del piloto, ciclo 2026-W38 con 8 pedidos verificados en Z-JM-01 (5 kg de papa amarilla, 10 kg de papa blanca y 10 kg de cebolla roja cada uno), y ciclo 2026-W39 para las propuestas (el sábado 19/09 todavía no abre).

| # | Criterio | Resultado |
|---|---|---|
| CX-A | El admin crea el transportista `reparto-1` con contraseña de 10 caracteres; entra con `tipo: transportista` | 201, luego 200 con `rol: transportista` |
| CX-B | Usuario `Reparto 1` | `INVALID_USER` |
| CX-C | Usuario `admin-yapa` (ya es admin) o uno ya creado | `USER_TAKEN` |
| CX-D | Contraseña de 9 caracteres | `INVALID_PASSWORD` |
| CX-E | Un vecino o un transportista intenta crear una cuenta | `NOT_AUTHORIZED` en el motor, 403 en la API |
| CX-F | Cuenta de proveedor para `SUP-OTRO` (no aliado) | `SUPPLIER_NOT_ALLIED` |
| CX-G | Cuenta de proveedor con código `SUP-NUEVO` y nombre "Mercado Mayorista Norte": se registra el proveedor aliado | aliado |
| CX-H | El admin desactiva `reparto-1`: la sesión abierta recibe 401 y el login da `INVALID_CREDENTIALS`; con contraseña nueva vuelve a entrar | 401, luego 200 |
| CX-I | El transportista pide `/api/admin/armado` o `/api/mis-pedidos`; el proveedor pide `/api/reparto` | 403 |
| TR-A | Con las 8 bolsas armadas, el transportista ve 1 parada (Z-JM-01) con 8 pedidos, cada uno con 1 bolsa, estado pendiente, y la respuesta no trae nombres de vecinos | 1 parada |
| TR-B | El transportista entrega Z-JM-01 con foto y "Sr. Ramos": la entrega queda con `delivered_by = reparto-1` y la parada pasa a entregada | entregada |
| TR-C | Con un pedido sin armar, la entrega da `ORDERS_NOT_PACKED` | `ORDERS_NOT_PACKED` |
| TR-D | Entrega fallida con motivo `PORTERIA_CERRADA` y foto | fallida |
| TR-E | El transportista intenta armar una bolsa | `NOT_AUTHORIZED` |
| TR-F | Un transportista desactivado intenta entregar desde el motor | `NOT_AUTHORIZED` |
| PV-A | El proveedor `SUP-FRESCOS` manda para W39 papa amarilla con tramos 0→3.40 y 100→3.20, máximo 300: queda pendiente y el catálogo de W39 no cambia | pendiente |
| PV-B | La misma lista el lunes 21/09 (W39 ya abrió) | `CATALOG_LOCKED` |
| PV-C | Una línea con proveedor `SUP-LIMPIEZA` | `FOREIGN_SUPPLIER` |
| PV-D | Un producto `LIMPIATODO-GALON` (es de `SUP-LIMPIEZA`) con proveedor vacío | `FOREIGN_PRODUCT` |
| PV-E | Tramos con precio que sube | `INVALID_TIERS` |
| PV-F | El admin aprueba: en W39 la papa amarilla tiene los tramos nuevos, los demás productos de `SUP-FRESCOS` que no mandó ya no están y `LIMPIATODO-GALON` sigue | publicado |
| PV-G | Aprobar dos veces | `OFFER_NOT_PENDING` |
| PV-H | Rechazar sin motivo; con motivo "Falta la cebolla" queda rechazada y el proveedor ve el motivo | `REASON_REQUIRED`, luego rechazada |
| PV-I | Reenviar después de rechazada: vuelve a pendiente | pendiente |
| PV-J | En W38 cerrado, `SUP-FRESCOS` ve papa amarilla 40 kg, papa blanca 80 kg y cebolla 80 kg con su tramo y monto, `parcial: false`; `SUP-LIMPIEZA` no ve esos productos | totales |
| PV-K | En W38 antes del cierre, el mismo pedido sale con `parcial: true` | parcial |

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| CX-01 | `partners._check_admin` | `test_cx_e_only_admin_creates`, `test_cx_e_neighbor_and_driver_cannot_create_accounts` |
| CX-02 | `partners._check_user` (S-279) | `test_cx_b_invalid_user`, `test_cx_c_user_taken` |
| CX-03 | `partners.create_driver`, `partners._check_password` | `test_cx_d_short_password`, `test_cx_d_driver_needs_name` |
| CX-04 | `partners.create_supplier_account` (S-283) | `test_cx_f_supplier_must_be_allied`, `test_cx_g_new_supplier_is_registered_as_allied` |
| CX-05 | `partners.deactivate` borra la credencial; `partners.set_password` reactiva; la sesión cae por SG-05 | `test_cx_h_deactivated_account_cannot_log_in_until_new_password`, `test_cx_h_deactivation_closes_session` |
| CX-06 | `web/api.py` `KINDS`, `role_of` y el chequeo de rol de `dispatch` | `test_cx_i_each_account_only_uses_its_routes` |
| TR-01 | `web/api.py` `reparto` (S-282) | `test_tr_a_route_without_neighbor_data` |
| TR-02, TR-03 | `fulfillment.check_courier` en `deliver_zone` y `register_failed_delivery`; rutas `/api/reparto/entregas*` | `test_tr_b_*`, `test_tr_c_cannot_deliver_unpacked_orders`, `test_tr_d_*`, `test_tr_f_*` |
| TR-04 | `pack_bag` sigue con `check_staff` | `test_tr_e_driver_does_not_pack` |
| PV-01..PV-03 | `supplier_offers.submit_offer` | `test_pv_a_*`, `test_pv_b_cycle_already_open`, `test_pv_c_foreign_supplier_column`, `test_pv_d_foreign_product`, `test_pv_e_invalid_tiers`, `test_pv_only_supplier_accounts_send_offers` |
| PV-04 | `supplier_offers.approve_offer` (usa `publish_catalog`) | `test_pv_f_*`, `test_pv_g_cannot_approve_twice` |
| PV-05 | `supplier_offers.reject_offer` | `test_pv_h_reject_needs_reason`, `test_pv_i_resend_after_rejection_is_pending_again` |
| PV-06 | `supplier_offers.supplier_order`; `web/api.py` `proveedor` | `test_pv_j_*`, `test_pv_k_partial_before_close`, `test_pv_offer_flow_from_api` |

Web: el acceso del equipo tiene un selector Equipo · Reparto · Proveedor (`AuthDialog.tsx`); el reparto y el proveedor ven solo su pantalla (`PartnerPanel.tsx`), y el panel del equipo suma la sección "Proveedores y reparto" para crear cuentas y revisar listas (`AdminPanel.tsx`). La demo local crea `reparto-demo` y `frescos-demo` (`web/__main__.py`).

Hallazgo al probar: en la prueba de la API, la sesión vencía al pasar el reloj del negocio del viernes al sábado; se le dio a la prueba un reloj de sesiones propio (DM-05), sin cambiar las reglas.

Evidencia: `docs/evidencia/desarrollo/54-proveedores-transportistas-rojo.txt` (el módulo no existía) y `54-proveedores-transportistas-verde.txt`.


# Yapa — CUS-06 Preparar pedidos (armado)

**Fuente de las reglas:** `api/docs/desarrollo/07-armado-entrega-reclamos.md` (AR, S-41), `21-huecos-armado-colchon.md` y `55-personal-por-rol.md` (AM, S-290) y `56-compra-real-y-armado.md` (DA, RT, S-297, S-298).

**Estado:** completo (iteración 56): armado con foto por bolsa, rótulo de cada bolsa y dañados al armar (colchón primero; si no alcanza, se devuelve en la liquidación).

## 0. Objetivo y frontera

Armar las bolsas de cada pedido que se va a atender, con una foto por bolsa como evidencia, para que la entrega de la zona salga completa.

Actores: **armador** (cuenta propia) y **administrador**.

## 1. Requerimientos funcionales

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-06.1 | El armador ve la lista de armado: pedido, vecino, productos y bolsas, sin montos ni datos de pago. | AM-01, S-290 | La respuesta no tiene `total`, `pago` ni `codigo_pago`. |
| RF-06.2 | Solo se arma después del cierre y solo un pedido que se va a atender (pago verificado, no cancelado, grupo con mínimo). | AR-03, AR-04, S-41 | Antes del cierre → `CYCLE_STILL_OPEN`; grupo con 7 → `ORDER_NOT_ATTENDED`. |
| RF-06.3 | Cada bolsa lleva una foto; las bolsas se numeran 1, 2, 3… | AR-05, S-151 | Sin foto → `PHOTO_REQUIRED`. |
| RF-06.4 | Solo el armador o el administrador registran bolsas. | AR-01, AM-02 | Transportista o armador desactivado → `NOT_AUTHORIZED`. |
| RF-06.5 | Cada bolsa tiene su rótulo "Pedido N · Zona · Bolsa n de T". | RT-01, S-298 | Pedido 1 con dos bolsas → "Pedido 1 · Residencial San Felipe · Bolsa 1 de 2" y "… 2 de 2". |
| RF-06.6 | El armador registra un artículo dañado con foto, con la compra ya registrada y antes de entregar la zona. Se repone con el colchón o se devuelve en la liquidación, sin que el vecino reclame. | DA-01..DA-06, S-297 | Sin compra → `PURCHASE_NOT_REGISTERED`; pasarse de lo pedido → `INVALID_DAMAGED_ITEM`. |

## 2. Ficha

| Campo | Descripción |
|---|---|
| Identificador | CUS-06 |
| Actores | Armador (principal), administrador |
| Disparador | Llega la compra del proveedor (jueves o viernes). |
| Precondiciones | Ciclo cerrado; pedidos atendidos. |
| Postcondición de éxito | Cada pedido atendido tiene al menos una bolsa con foto y `packed_by` con el usuario que la armó. |

## 3. Flujo principal

| Paso | Armador | Sistema |
|---|---|---|
| 1 | Abre "Armado" y elige la zona. | Lista los pedidos por armar de la zona con sus productos. |
| 2 | Arma la bolsa y le toma una foto con el celular. | — |
| 3 | Registra la bolsa. | Valida cierre, pedido atendido y foto; guarda la bolsa con su número. |
| 4 | Repite hasta terminar la zona. | La zona se puede entregar cuando todos sus pedidos tienen al menos una bolsa (EN-05). |

## 4. Flujos alternativos y excepciones

| Código | Condición | Respuesta |
|---|---|---|
| FA-01 | El ciclo sigue abierto. | `CYCLE_STILL_OPEN`. |
| FA-02 | El pedido no se atiende (sin pago, cancelado o grupo bajo el mínimo). | `ORDER_NOT_ATTENDED`. |
| FA-03 | Falta la foto. | `PHOTO_REQUIRED`. |
| FA-04 | Un artículo llegó dañado. | "Algo llegó dañado": se repone desde el colchón o pasa como faltante a la liquidación (DA-06). |
| EX-01 | La zona ya se entregó o falló. | `ZONE_ALREADY_CLOSED`; lo que falte va por reclamo (AR-06, S-121). |

## 5. Escenarios de aceptación

1. **Armar.** Dos bolsas con foto de un pedido → bolsas 1 y 2. (AR-A)
2. **Antes del cierre.** Miércoles 16/09 a las 19:59 → `CYCLE_STILL_OPEN`. (AR-C)
3. **Armador.** El armador ve los 8 pedidos de Z-JM-01 sin montos y registra la bolsa del primero → `packed_by = armado-1`. (AM-A)

## 6. Pantallas y código

- Web: panel → Armado (`PhotoForm.tsx` para la foto).
- API: `/api/admin/armado` (con `rotulos`), `/api/admin/bolsas`, `/api/admin/danados`.
- Motor: `fulfillment.pack_bag`, `fulfillment.bag_labels`, `purchase.register_damaged`.

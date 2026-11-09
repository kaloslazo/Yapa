# Yapa — CUS-07 Entregar en la zona

**Fuente de las reglas:** `api/docs/desarrollo/07-armado-entrega-reclamos.md` (EN, S-42), `16-entrega-fallida-cierre.md` (EF), `54-proveedores-y-transportistas.md` (TR, S-282) y `55-personal-por-rol.md` (PO, S-293, S-294).

**Estado:** completo. Reparto del transportista, entrega con foto, entrega fallida, confirmación de la portería y bloqueo del despacho hasta registrar la compra (iteración 56). **El cálculo de rutas queda fuera del alcance** (decisión del 09/11/2026): con pocas zonas en el piloto, el orden de paradas se arma a mano.

## 0. Objetivo y frontera

Llevar el sábado las bolsas de cada zona a su punto de recepción (portería o encargado), dejar evidencia de la entrega o de la falla, y que el edificio confirme que las recibió.

Actores: **transportista** (cuenta propia), **portería** (cuenta por zona), **admin de zona** y **administrador**.

## 1. Requerimientos funcionales

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-07.1 | El transportista ve las paradas del ciclo con zona, distrito, quién recibe, contacto, ubicación y, por pedido, solo el número y las bolsas. | TR-01, S-282 | No ve nombres de vecinos, celulares ni montos. |
| RF-07.2 | La entrega es por zona y todo o nada: todos los pedidos atendidos de la zona deben tener bolsa. | EN-04, EN-05, S-42 | 7 de 8 armados → `ORDERS_NOT_PACKED`. |
| RF-07.3 | La entrega exige la foto y el nombre de quien recibe, y guarda la hora. | EN-03 | Sin foto → `PHOTO_REQUIRED`; sin quien recibe → `RECEIVER_REQUIRED`. |
| RF-07.4 | Si nadie recibe, se registra la entrega fallida con foto y motivo (`PORTERIA_CERRADA`, `NADIE_RECIBE`, `PORTERIA_RECHAZA`), sin reintento. | EF-01..EF-03, S-102, S-105 | Motivo `LLUVIA` → `INVALID_FAILURE_REASON`. |
| RF-07.5 | Una zona se entrega o falla una sola vez por ciclo. | EN-02, EF-03 | La segunda vez → `ZONE_ALREADY_CLOSED`. |
| RF-07.6 | La portería de la zona o su admin confirman la recepción una sola vez, y cada vecino recibe el aviso "Tus bolsas ya están en el edificio". | PO-02..PO-04, S-294 | Portería de otra zona → `FOREIGN_ZONE`; confirmar dos veces → `ALREADY_CONFIRMED`. |
| RF-07.7 | La portería ve las entregas de su zona con el nombre del vecino y sus bolsas, sin productos, montos ni celulares. | PO-01, S-293 | — |
| RF-07.8 | Una zona no se entrega ni se marca como fallida hasta que compras registre la compra real del ciclo. | BD-01, S-299 | Sin compra → `PURCHASE_NOT_REGISTERED`. |

## 2. Ficha

| Campo | Descripción |
|---|---|
| Identificador | CUS-07 |
| Actores | Transportista (principal), portería, admin de zona, administrador |
| Disparador | Sábado en la ventana asignada a la zona. |
| Precondiciones | Pedidos de la zona armados (CUS-06). |
| Postcondición de éxito | Zona `entregada` (y luego `recibida`) con foto, quien recibe y hora; los vecinos reciben el aviso. Con falla: zona `fallida`, que en la liquidación devuelve todo menos el envío real (CUS-04). |
| Garantía ante fallo | Si falta una bolsa, no se registra nada para la zona. |

## 3. Flujo principal

| Paso | Actor | Sistema |
|---|---|---|
| 1 | El transportista abre "Reparto". | Lista las paradas del ciclo con su estado (pendiente, entregada o fallida). |
| 2 | Llega a la zona, deja las bolsas y toma la foto. | — |
| 3 | Registra la entrega con el nombre de quien recibe. | Valida que todo esté armado, guarda foto, receptor y hora, y avisa a los vecinos. |
| 4 | La portería (o el admin de zona) abre su panel y confirma la recepción. | Marca la entrega `recibida` y avisa a cada vecino. |

## 4. Flujos alternativos y excepciones

| Código | Condición | Respuesta |
|---|---|---|
| FA-01 | Nadie recibe. | El transportista registra la falla con foto y motivo; la zona queda `fallida`. |
| FA-02 | Falta armar un pedido. | `ORDERS_NOT_PACKED`; la zona sigue pendiente. |
| FA-03 | La zona no tiene pedidos atendidos. | `NOTHING_TO_DELIVER`. |
| FA-04 | Compras todavía no registra lo que llegó. | `PURCHASE_NOT_REGISTERED`; la zona espera. |
| EX-01 | Se intenta entregar o fallar dos veces. | `ZONE_ALREADY_DELIVERED` / `ZONE_ALREADY_CLOSED`. |
| EX-02 | Confirma una portería de otra zona o un vecino que no administra la zona. | `FOREIGN_ZONE` / `NOT_AUTHORIZED`. |

## 5. Escenarios de aceptación

1. **Entregar.** Con los 8 pedidos armados, foto y "Sr. Ramos" → entrega registrada el sábado a las 09:00. (EN-A)
2. **Todo o nada.** Con 7 de 8 armados → `ORDERS_NOT_PACKED`. (EN-B)
3. **Falla.** `PORTERIA_CERRADA` con foto → registrada; volver a entregar → `ZONE_ALREADY_CLOSED`. (EF-A)
4. **Sin datos de vecinos.** El reparto del transportista no trae nombres, celulares ni montos. (TR-A)
5. **Recepción.** La portería de Los Álamos confirma → cada vecino recibe el aviso; confirmar otra vez → `ALREADY_CONFIRMED`. (PO-B, PO-C)

## 6. Pantallas y código

- Web: panel del transportista y de la portería (`PartnerPanel.tsx`), tarjeta de recepción en la zona (`ReceptionCard.tsx`).
- API: `/api/reparto`, `/api/reparto/entregas`, `/api/reparto/entregas-fallidas`, `/api/admin/entregas*`, `/api/porteria`, `/api/porteria/recepciones`, `/api/zona/recepcion`.
- Motor: `fulfillment.deliver_zone`, `fulfillment.register_failed_delivery`, `reception.py`.

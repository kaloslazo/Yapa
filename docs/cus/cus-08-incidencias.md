# Yapa — CUS-08 Reclamos e incidencias

**Fuente de las reglas:** `api/docs/desarrollo/07-armado-entrega-reclamos.md` (RC, RV, S-43..S-45), `16-entrega-fallida-cierre.md` (EF-05), `33-admin-foto-confirmaciones.md` `55-personal-por-rol.md` (AT) y `56-compra-real-y-armado.md` (IN, S-300). Decisión C-10.

**Estado:** completo: reclamo por artículo, revisión por atención e incidencias de atención (iteración 56).

## 0. Objetivo y frontera

Permitir que el vecino reclame, dentro de las 24 h siguientes a la entrega, un artículo faltante o dañado con foto, y que atención lo revise y devuelva su valor como saldo, sin pagar dos veces lo que ya se descontó en la liquidación.

Actores: **vecino** (reclama) y **atención** o **administrador** (revisan).

## 1. Requerimientos funcionales

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-08.1 | Solo el dueño de un pedido entregado reclama, dentro de las 24 h desde la entrega de su zona. | RC-01..RC-03, S-43 | A las 24 h exactas → `CLAIM_WINDOW_CLOSED`; pedido ajeno → `ORDER_NOT_FOUND`. |
| RF-08.2 | El reclamo es por artículo, con motivo `FALTANTE` o `DANADO`, foto y cantidad en el paso del producto, sin pasar de lo pedido. | RC-04, RC-05, S-44 | 1,5 kg o un producto que no está en el pedido → `INVALID_CLAIM_ITEM`. |
| RF-08.3 | El reclamo queda `PENDIENTE` y no mueve dinero hasta que se revisa. | RC-06 | El saldo no cambia al reclamar. |
| RF-08.4 | Atención aprueba solo con el ciclo liquidado; abona precio final × cantidad, redondeado a favor del vecino. | RV-03, RV-05, S-45 | Sin liquidar → `CYCLE_NOT_SETTLED`. |
| RF-08.5 | No se aprueba lo que ya se descontó como faltante en la liquidación. | RV-04 | → `INVALID_CLAIM_ITEM`. |
| RF-08.6 | Un pedido de una zona fallida no se reclama: ya recibió todo como saldo. | EF-05 | → `ORDER_NOT_DELIVERED`. |
| RF-08.7 | Atención ve la foto del reclamo antes de decidir. | iteración 33 | Solo el personal ve la foto. |
| RF-08.8 | Atención registra incidencias sobre un pedido (entrega, bolsa, trato u otro) y las cierra con una nota. No mueven dinero: si hay que devolver, va por reclamo o devolución. | IN-01..IN-04, S-300 | Tipo `QUEJA` o texto de 501 caracteres → `INVALID_INCIDENT`; cerrar dos veces → `INCIDENT_ALREADY_CLOSED`. |

## 2. Ficha

| Campo | Descripción |
|---|---|
| Identificador | CUS-08 |
| Actores | Vecino (principal), atención, administrador |
| Disparador | El vecino recibe su pedido y falta o llega dañado un artículo. |
| Precondiciones | Pedido entregado (CUS-07) hace menos de 24 h. |
| Postcondición de éxito | Reclamo `APROBADO` con el saldo abonado, o `RECHAZADO` sin mover dinero. |

## 3. Flujo principal

| Paso | Actor | Sistema |
|---|---|---|
| 1 | El vecino abre su pedido entregado y toca "Reclamar". | Muestra los artículos del pedido. |
| 2 | Elige el artículo, el motivo y la cantidad, y sube la foto. | Valida plazo, dueño, motivo, foto y cantidad; guarda el reclamo `PENDIENTE`. |
| 3 | Atención abre "Reclamos" y mira la foto. | — |
| 4 | Aprueba. | Verifica que el ciclo esté liquidado y que no se devuelva dos veces; abona el saldo y avisa al vecino. |

## 4. Flujos alternativos y excepciones

| Código | Condición | Respuesta |
|---|---|---|
| FA-01 | Atención rechaza. | `RECHAZADO`; el vecino puede volver a reclamar dentro del plazo. |
| FA-02 | El ciclo aún no se liquida. | `CYCLE_NOT_SETTLED`; el reclamo sigue pendiente. |
| EX-01 | Fuera de plazo. | `CLAIM_WINDOW_CLOSED`. |
| EX-02 | Motivo inválido o sin foto. | `INVALID_CLAIM_REASON` / `PHOTO_REQUIRED`. |
| EX-03 | Revisar dos veces. | `CLAIM_ALREADY_REVIEWED`. |

## 5. Escenarios de aceptación

1. **A tiempo.** Domingo 20/09 a las 08:59 reclama 1 kg de cebolla `DANADO` con foto → `PENDIENTE`, saldo igual. (RC-A)
2. **Fuera de plazo.** Domingo 20/09 a las 09:00 → `CLAIM_WINDOW_CLOSED`. (RC-B)
3. **Aprobar.** Con el ciclo liquidado se aprueba → el saldo sube S/ 2,02 (2,016 redondeado a su favor). (RV-A)
4. **Sin doble devolución.** La liquidación ya descontó la cebolla como faltante → aprobar da `INVALID_CLAIM_ITEM`. (RV-E)

## 6. Pantallas y código

- Web: Mis pedidos → Reclamar (`OrdersPage.tsx`, `PhotoForm.tsx`); panel → Reclamos.
- API: `/api/reclamos`, `/api/admin/reclamos`, `/api/admin/reclamos/{id}/revisar`, `/api/admin/foto`, `/api/admin/incidencias`, `/api/admin/incidencias/{id}/cerrar`.
- Motor: `claims.file_claim`, `claims.review_claim`, `incidents.py`.

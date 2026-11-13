# Iteración 65 · Los pedidos y los reclamos del vecino, como un carrito

## Requisito

Como vecino, quiero ver lo que pedí con la foto de cada producto, como en el carrito de un supermercado, y reclamar algo tocando el producto que faltó o llegó mal, en lugar de buscarlo en una lista de texto. También quiero ver mis reclamos con su producto y en qué quedaron.

## Por qué

En la demo del 12/11/2026, el reclamo se veía como un historial de pedidos en texto: un desplegable "Pedido 2 · Papa amarilla (8)" donde aparecían también pedidos de semanas pasadas, que ya no se pueden reclamar (RC-03: 24 horas desde la entrega). Elegir uno de esos daba un error recién al enviar.

## Alcance

Pantalla del vecino (Mis pedidos). La regla de las 24 horas no cambia: solo se deja de ofrecer lo que ya no se puede reclamar.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-333 | Los productos de cada pedido se ven como en un carrito: foto, nombre, cantidad y precio máximo de la línea. | — |
| S-334 | `GET /api/reclamos` ofrece para reclamar solo los productos de pedidos entregados hace menos de 24 horas (la misma ventana de RC-03), y cada opción dice hasta cuándo se puede reclamar (`hasta`). Los pedidos más viejos ya no aparecen como opción. | 24 h |
| S-335 | El reclamo se arma tocando la tarjeta del producto (con su foto), eligiendo la cantidad, el motivo (faltó o llegó dañado) y tomando la foto. "Tus reclamos" muestra cada reclamo con la foto del producto, el motivo, el estado y cuánto volvió al saldo. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| RV-01 | Una opción para reclamar aparece solo si su pedido se entregó y no pasaron 24 horas desde la entrega (S-334). | — |
| RV-02 | Cada opción trae `hasta`, la hora límite en ISO 8601 (entrega + 24 h). | — |
| RV-03 | Los reclamos del vecino traen el `nombre` del producto (OC-03). | — |

## Criterios de aceptación

Escenario base: Residencial San Felipe, 8 pedidos entregados el sábado 19/09 a las 10:00.

- **RV-A · Dentro de las 24 horas.** El sábado a las 11:00, el dueño del pedido 1 recibe sus 3 productos para reclamar, cada uno con `hasta` "2026-09-20T10:00:00-05:00". → RV-01, RV-02
- **RV-B · Pasadas las 24 horas.** El domingo a las 10:00 ya no recibe opciones; sus reclamos anteriores siguen en la lista con el `nombre` del producto. → RV-01, RV-03
- **RV-C · El carrito del pedido.** En Mis pedidos, cada línea del pedido muestra la foto del producto, su nombre y su cantidad. → S-333
- **RV-D · Reclamar tocando.** El formulario no tiene un desplegable: hay una tarjeta por producto reclamable; al tocar la segunda y enviar, el reclamo va con su pedido y su producto. → S-335
- **RV-E · Tus reclamos.** Un reclamo aprobado de 1 kg de cebolla roja se ve con "Cebolla roja", "Llegó dañado", "Aprobado" y lo que volvió al saldo. → S-335

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| RV-01, RV-02, S-334 | `web/api.py` `reclamos` (ventana `claims.CLAIM_WINDOW`, campo `hasta`) | `test_reclamos_carrito_65.test_rv_a_*`, `test_rv_b_*` |
| RV-03 | `claim_json` con `nombre` (OC-03) | `test_rv_b_*` |
| S-333 | `OrdersPage.tsx`: lista `order-cart` con `ProductThumb` | `reclamosCarrito.test.ts` RV-C |
| S-335 | `ClaimForm` (tarjetas `claim-pick` con radio) y `ClaimHistory` en `OrdersPage.tsx`; `App.tsx` pasa `hasta` y `nombre` | RV-D, RV-E |

## Evidencia

- `65-motor-rojo.txt` y `65-web-rojo.txt`: 2 pruebas del motor y 3 de la web fallan antes del código.
- `65-motor-verde.txt`: 733 pruebas del motor en verde.
- `65-web-verde.txt`: TypeScript, 179 pruebas de la web y build en verde.
- Revisión en un celular de 390 px (demo local, sábado 03/10 18:00): Carmen ve solo los 5 productos del pedido 12, cada uno con foto y hora límite; el pedido 2 de la semana anterior ya no aparece para reclamar; su reclamo de limón se ve con foto y estado.

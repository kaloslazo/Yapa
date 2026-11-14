# Iteración 67 · Cantidades con su unidad

## Requisito

Como armador, quiero leer "8 kg" o "2 unidades" y no solo "8", para meter en la bolsa la cantidad correcta. Como vecino, quiero ver lo mismo en mi pedido y al reclamar.

## Por qué

En la revisión del 12/11/2026, las tarjetas de armado, el carrito del pedido y las tarjetas para reclamar mostraban la cantidad sin unidad ("Papa amarilla 8", "Limpiatodo galón 2"). El motor conoce la unidad de cada producto (kg o unidad), pero las líneas del pedido no la traían.

## Alcance

Dato de lectura nuevo en la API y su uso en pantalla. No cambia ninguna regla.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-338 | Cada línea de un pedido trae la `unidad` del producto según el catálogo de su semana (`kg` o `unidad`). Las pantallas muestran "8 kg", "0.5 kg", "1 unidad" o "2 unidades". | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| UN-01 | Las líneas de los pedidos (`/api/mis-pedidos`, resumen, armado) traen `unidad`. El armador también la recibe. | — |
| UN-02 | Las opciones para reclamar traen `unidad`. | — |

## Criterios de aceptación

Escenario base: 8 pedidos de Residencial San Felipe, cada uno con 5 kg de papa amarilla, 10 kg de papa blanca y 10 kg de cebolla roja.

- **UN-A · Pedido.** Las líneas del pedido 1 en el resumen del admin traen `unidad` "kg". → UN-01
- **UN-B · Armado.** El armador recibe las líneas con `id`, `nombre`, `cantidad` y `unidad`. → UN-01
- **UN-C · Reclamar.** Las opciones para reclamar traen `unidad` "kg". → UN-02
- **UN-D · Pantallas.** La tarjeta de armado dice "5 kg" y "2 unidades"; el carrito del pedido y la tarjeta para reclamar dicen "5 kg". → S-338

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| UN-01 | `web/api.py` `units_for` y `order_json` (línea con `unidad`); `admin_armado` deja pasar `unidad` al armador | `test_cantidades_unidad_67.test_un_a_*`, `test_un_b_*` |
| UN-02 | `reclamos` con `unidad` | `test_un_c_*` |
| S-338 | `amountWithUnit` en `utils/format.ts`; `PackCard` (AdminPanel), carrito y reclamo de `OrdersPage.tsx`; `toLine` y `App.tsx` leen `unidad` | `cantidadesUnidad.test.ts` UN-D |

## Evidencia

- `67-motor-rojo.txt` y `67-web-rojo.txt`: 3 pruebas del motor y 2 de la web fallan antes del código.
- `67-motor-verde.txt`: 736 pruebas del motor en verde.
- `67-web-verde.txt`: TypeScript, 185 pruebas de la web y build en verde.
- En la demo local, la tarjeta de armado dice "10 kg" y "2 unidades"; el recorrido en Chrome sigue con 25 de 25 comprobaciones en verde.

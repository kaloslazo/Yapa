# Yapa — CUS-05 Compra al proveedor

**Fuente de las reglas:** `api/docs/desarrollo/54-proveedores-y-transportistas.md` (PV-06, S-288), `55-personal-por-rol.md` (CP, S-291), `56-compra-real-y-armado.md` (CR, S-295, S-296), `07-armado-entrega-reclamos.md` (CO, S-46) y `21-huecos-armado-colchon.md`. Decisión C-12.

**Estado:** completo (iteración 56). La compra real reparte el faltante del proveedor: primero el colchón y lo que no alcance se descuenta a los últimos pedidos, que lo reciben como saldo en la liquidación.

## 0. Objetivo y frontera

Con los pedidos cerrados, decir a cada proveedor aliado cuánto se le compra de cada producto y a qué tramo, y reponer faltantes no perecibles desde un colchón de inventario con tope.

Actores: **compras** (cuenta propia desde la iteración 55), **administrador** y **proveedor aliado** (ve lo que se le compra). Yapa no tiene inventario propio salvo el colchón de limpieza.

## 1. Requerimientos funcionales

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-05.1 | Compras ve, por proveedor, la cantidad total de cada producto en los pedidos que se atienden, el tramo alcanzado, el precio del tramo (sin comisión) y el monto. | CP-01, S-288, S-291 | Antes del cierre del miércoles el número se marca como parcial. |
| RF-05.2 | El proveedor ve lo mismo, solo de sus productos y sin datos de vecinos. | PV-06 | No ve pedidos sueltos ni nombres. |
| RF-05.3 | Compras guarda productos no perecibles en el colchón, con un tope de S/ 500 a precio del primer tramo. | CP-02, CO-02..CO-04, S-46 | Papa → `PERISHABLE_NOT_ALLOWED`; pasar el tope → `BUFFER_LIMIT_EXCEEDED`. |
| RF-05.4 | Compras repone el faltante de un pedido desde el colchón, sin pasar de lo pedido. | CP-03, CO-05, S-122 | Más de lo guardado → `BUFFER_INSUFFICIENT`. |
| RF-05.5 | Solo compras o el administrador tocan el colchón. | CP-04 | El armador → `NOT_AUTHORIZED`. |
| RF-05.7 | Yapa contrata y paga el flete de la compra, porque el proveedor no entrega. Compras registra la empresa y el monto una vez por semana; el margen real lo reparte entre los pedidos atendidos (sin registrar, S/ 180 estimados). | FL-01..FL-04, MR-01, S-306, S-307 | S/ 120 entre 8 pedidos → S/ 15,00 por pedido. |
| RF-05.6 | Compras registra, una vez por ciclo y después del cierre, lo que llegó del proveedor. El faltante se cubre primero con el colchón y el resto se descuenta desde el último pedido registrado; vuelve como saldo en la liquidación. El tramo sigue calculado con lo pedido. | CR-01..CR-06, S-295, S-296 | Llegan 36 kg de papa de 40 → el pedido 8 tiene 4 kg de faltante. Registrar dos veces → `PURCHASE_ALREADY_REGISTERED`. |

## 2. Ficha

| Campo | Descripción |
|---|---|
| Identificador | CUS-05 |
| Actores | Compras (principal), administrador, proveedor aliado |
| Disparador | Cierre del ciclo (miércoles 20:00). |
| Precondiciones | Catálogo del ciclo publicado (CUS-01); pedidos verificados (CUS-03). |
| Postcondición de éxito | Compras conoce el pedido consolidado por proveedor; el colchón queda registrado con su valor. |

## 3. Flujo principal

| Paso | Compras | Sistema |
|---|---|---|
| 1 | Abre "Compras" y elige el ciclo. | Muestra cada proveedor con sus productos: cantidad, tramo, precio y monto, y el colchón con su tope. |
| 2 | Envía el pedido al proveedor (fuera del sistema). | — |
| 3 | Recibe la mercadería y registra en "Lo que llegó" solo lo que vino de menos. | Reparte el faltante (colchón primero, luego desde el último pedido) y lo muestra por pedido. Desde ahora el reparto puede salir (S-299). |
| 4 | Si después falta algo más, repone desde el colchón para un pedido. | Valida pedido, cantidad y existencias; baja el valor del colchón en proporción. |

## 4. Flujos alternativos y excepciones

| Código | Condición | Respuesta |
|---|---|---|
| FA-01 | Ciclo todavía abierto. | El consolidado se marca como parcial. |
| FA-02 | Producto perecible al colchón. | `PERISHABLE_NOT_ALLOWED`. |
| FA-03 | Colchón lleno. | `BUFFER_LIMIT_EXCEEDED`; el valor no cambia. |
| FA-04 | Reponer más de lo que hay o de lo que pidió el vecino. | `BUFFER_INSUFFICIENT` o `BUFFER_NOT_FOR_ORDER`. |
| FA-05 | Lo recibido es mayor que lo pedido, negativo o fuera del paso. | `INVALID_PURCHASE_ITEM`; no se registra nada. |

## 5. Escenarios de aceptación

1. **Consolidado.** Compras ve la compra de W39 por proveedor con tramo y monto. (CP-A)
2. **Tope.** 60 galones de limpiatodo (S/ 474) + 4 de lejía (S/ 26) = S/ 500 → se acepta; un galón más → `BUFFER_LIMIT_EXCEEDED`. (CO-B)
3. **Reponer.** De 6 galones se usan 2 → quedan 4 con valor S/ 31,60. (CO-D)
4. **Faltante que pasa de un pedido.** Llegan 33 kg de papa de 40 → el pedido 8 pierde 5 kg y el 7 pierde 2 kg. (CR-B)
5. **Colchón primero.** Con 3 galones guardados y 4 de faltante → el colchón cubre 2 del pedido 8 y 1 del 7; el pedido 7 tiene 1 galón de faltante. (CR-C)

## 6. Pantallas y código

- Web: panel de compras; panel del proveedor (`PartnerPanel.tsx`).
- API: `/api/compras`, `/api/compras/recibido`, `/api/compras/colchon`, `/api/compras/colchon/usar`, `/api/proveedor`.
- Motor: `supplier_offers.supplier_order`, `purchase.register_purchase`, `buffer.py`.

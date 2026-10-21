# Iteración 31 · Pulido de la tienda: dinero con confirmación y compra cómoda en el celular

## Requisito

Como vecino, quiero que ninguna acción con mi dinero se ejecute con un toque mal dado, y quiero comprar desde el celular viendo siempre cuánto llevo y cuánto me falta para el mínimo.

## Por qué

Auditoría de diseño del 18/10/2026 sobre la tienda (tres roles, revisión de código y recorrido en navegador a escritorio y a 390 px):

- Cancelar un pedido y pedir "devolverme todo" a Yape o Plin se ejecutaban al primer toque, y los dos botones de cancelar casi no se distinguían.
- En el celular la canasta queda al final de la página (a 3915 px de 5238 px) y el botón "Continuar pedido" no está al alcance del pulgar.
- Los botones de más y menos de cada producto miden 30 px (el mínimo recomendado para el dedo es 44 px).
- En el celular la pestaña "Canasta" del menú se corta y no hay señal de que el menú se desliza.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-172 | Cancelar un pedido y devolver el saldo a Yape o Plin piden una confirmación en la misma pantalla, que dice a dónde va el dinero y cuánto tarda. No hay confirmación para acciones que no mueven dinero. | — |
| S-173 | La barra fija de la canasta se muestra solo en el celular (pantalla de 860 px o menos), solo en la tienda y solo si hay productos. Muestra cantidad, total de productos y, si falta, cuánto para el mínimo. | — |
| S-174 | Los botones que se tocan con el dedo (más, menos, pestañas, "Agregar", navegación) miden al menos 44 px de alto. | 44 px |

## Reglas

| Regla | Comportamiento |
|---|---|
| UI-01 | "Cancelar pedido" abre una confirmación con dos elecciones claras: **a mi saldo** (se usa en el próximo pedido, no vence) o **a mi Yape o Plin** (hasta 30 días). Cada elección dice su plazo con palabras. Hay un "No cancelar" que cierra la confirmación sin hacer nada. |
| UI-02 | "Devolverme todo a mi Yape o Plin" pide confirmar mostrando el monto y el plazo de 30 días. |
| UI-03 | Mientras se envía la acción, los botones quedan desactivados (una sola vez). |
| UI-04 | En el celular, con productos en la canasta, una barra fija abajo muestra `N productos · S/ total` y el mensaje del mínimo. Con el mínimo cumplido el botón es **Continuar pedido** (abre el pedido). Sin el mínimo el botón es **Ver canasta** (baja a la canasta). |
| UI-05 | La barra no tapa el pie de la página ni los avisos: la página deja espacio debajo. |
| UI-06 | `minimumGap(subtotal, minimo)` devuelve cuánto falta para el mínimo, nunca menos de 0 y redondeado a centavos. |
| UI-07 | `refundPromise(destino, medio)` devuelve el texto del plazo: saldo = "queda en tu saldo, no vence"; medio de pago = "te lo devolvemos a tu Yape o Plin en hasta 30 días". |
| UI-08 | Los botones táctiles miden al menos 44 px de alto (S-174). Los de cantidad dentro de la canasta incluidos. |
| UI-09 | En el celular el menú superior deja ver parte de la siguiente opción (no se corta sin pista) y la opción activa queda a la vista. |

## Fuera de esta iteración

- Mostrar la foto del reclamo al admin de Yapa: hoy la API no entrega las fotos guardadas. Necesita un endpoint solo para el admin con control de ruta (iteración 32, con su spec y pruebas del motor).
- Confirmar "Pedir unión" y "Separar mi zona" del admin de zona, y verificar pagos o aprobar reclamos del admin de Yapa (iteración 32).
- Accesibilidad (foco, contraste de textos grises, enlace de salto): iteración propia.
- Ventana de entrega del sábado y avisos por WhatsApp: necesitan regla de negocio del equipo.

## Criterios de aceptación (pruebas de `src/**/*.test.ts`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| UI-A | Falta para el mínimo | subtotal 32.50, mínimo 50 | 17.50 |
| UI-B | Mínimo cumplido | subtotal 50, mínimo 50 | 0 |
| UI-C | Nunca negativo | subtotal 80, mínimo 50 | 0 |
| UI-D | Redondeo a centavos | subtotal 49.995, mínimo 50 | 0.01 |
| UI-E | Plazo del saldo | destino SALDO | el texto dice que queda en el saldo y que no vence |
| UI-F | Plazo del medio de pago | destino MEDIO_DE_PAGO, medio YAPE | el texto dice "Yape" y "30 días" |
| UI-G | Medio Plin | destino MEDIO_DE_PAGO, medio PLIN | el texto dice "Plin" |

Las reglas de pantalla (UI-01..UI-05, UI-08, UI-09) se verifican en el navegador a 390 px y a escritorio; el resultado queda en el registro.

## Trazabilidad (regla → código → prueba)

| Regla | Código | Prueba |
|---|---|---|
| UI-01, UI-03 | `CancelActions` en `src/components/OrdersPage.tsx` | navegador a 390 px (pedido 12 de Carmen) |
| UI-02 | `confirmingWithdraw` en `OrdersPage` | navegador a 390 px (saldo de S/ 0.56) |
| UI-04, UI-05 | `MobileCartBar` en `src/components/CartPanel.tsx`, `App.tsx`, bloque de la iteración 31 en `styles.css` | navegador: con 1 producto dice "Te faltan S/ 45.97" y el botón "Ver canasta"; en escritorio la barra no se muestra |
| UI-06 | `minimumGap` en `src/utils/cart.ts` | UI-A..UI-D en `src/utils/refund.test.ts` |
| UI-07 | `refundPromise` en `src/utils/refund.ts` | UI-E..UI-G |
| UI-08 | `min-height: 44px` y zona de toque ampliada en `styles.css` | revisión de CSS; quedan fuera los enlaces de texto sueltos (accesibilidad, iteración propia) |
| UI-09 | degradado a la derecha del menú en `styles.css` | navegador: "Canasta" se ve difuminada, con pista de que hay más |

Evidencia: `docs/evidencia/desarrollo/31-pulido-rojo.txt` y `31-pulido-verde.txt` (13 pruebas del frontend, antes 6). Tipos y build sin errores. El motor no cambió (340 pruebas).

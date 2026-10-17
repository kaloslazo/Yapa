# Iteración 29 · Frontend de Kalos conectado al motor: vecino, admin de zona y admin de Yapa

## Requisito

Como vecino, quiero comprar en la tienda de Yapa (la de Kalos) con las reglas reales: avance del tramo, ahorro frente al supermercado, pago sin escribir códigos, mis pedidos con lo que me devolvieron, mis reclamos y mi zona.

Como admin de zona, quiero un panel propio para ver cómo va mi edificio, invitar vecinos, unir mi zona con una cercana y transferir el rol.

Como admin de Yapa, quiero operar la semana completa desde el panel de Kalos: verificar, armar con foto, entregar, liquidar, resolver reclamos y devoluciones, ver la conciliación y las métricas, publicar el catálogo y dar de alta vecinos.

## Por qué

- Decisión del equipo (17/10/2026): la cara es el React de Kalos y las reglas viven en un solo lugar, el motor de `api/` (iteración 27).
- Pedido de Carlos: nada de pantallas para escribir. Se elige con botones, listas y casillas; solo se escribe lo que no se puede elegir (PIN, montos, nombres).

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-166 | El frontend **no calcula reglas**. Precios, totales, ahorro, liquidación, beneficios y permisos vienen de la API. Solo suma el carrito en el navegador para mostrarlo mientras se arma (como S-144); el total que vale lo da `POST /api/cotizar`. | — |
| S-167 | No hay registro libre con correo: el alta la hace el admin de Yapa con el consentimiento del vecino (S-133). La tienda explica cómo pedir el alta y con qué código de referido. | — |
| S-168 | Se retiran de esta rama el servicio de Appwrite, la copia en TypeScript de las reglas (`utils/domain.ts`) y sus pruebas, porque las reglas y sus pruebas viven en `api/`. Quedan en el historial de Git (commits de Kalos del 17/10). | — |
| S-169 | Los productos sin foto propia se muestran con un ícono grande sobre el fondo de color de su tipo, en el mismo estilo de las tarjetas de Kalos. | — |

## Reglas

| Regla | Comportamiento |
|---|---|
| FE-01 | Todos los datos vienen de `/api` (S-166). En desarrollo Vite reenvía `/api` al motor en el puerto 8000 (S-153). |
| FE-02 | Entrar: vecino con número de cliente y PIN; admin con usuario y contraseña. Según el rol se abre la tienda, el panel de zona o el panel de operaciones. |
| FE-03 | Tienda: productos por categoría, con precio máximo, avance del grupo hacia el siguiente tramo, ahorro frente al supermercado y botones − y + que respetan el paso (0.25 kg en el ajo) y el máximo por pedido. |
| FE-04 | Pedido sin escribir: medio (Yape o Plin) y casilla "usar mi saldo". La confirmación muestra **cuánto yapear** y el **código de pago** con un botón para copiarlo (S-150). |
| FE-05 | Mis pedidos: avance, cancelar con botones, lo devuelto, el ahorro frente al supermercado, el beneficio de admin de zona, y reclamos con foto en los pedidos entregados. |
| FE-06 | Mi zona (vecino): su zona, unirse a otra de una lista, crear una con el botón de ubicación, y su código de referido con enlace para compartir por WhatsApp. |
| FE-07 | Panel del admin de zona: avance del grupo, vecinos con "ya pidió", beneficios, código de referido, mapa con el radio de 300 m y las zonas a 500 m, unir, aceptar o rechazar solicitudes, transferir el rol y activar la recepción. |
| FE-08 | Panel de operaciones (admin de Yapa): resumen con indicadores y grupos, verificar pagos, liquidar con confirmación, armado y entrega con foto, reclamos, devoluciones, conciliación, métricas, catálogo, precios de referencia y vecinos (alta con consentimiento y referido, reinicio de PIN). |

## Criterios de aceptación (pruebas de `src/**/*.test.ts`)

- **FE-A · Producto desde la API.** Un producto de la API con `precio_max` `"4.03"`, `paso` `"1"`, `pedido_total` `"27"` y siguiente tramo desde `"100"` a `"3.79"` se muestra con precio 4.03, avance 27 de 100 y "baja a 3.79". Con referencia de supermercado a `"7.99"`, el ahorro es 49.5 %.
- **FE-B · Paso y tope del carrito.** El ajo (paso 0.25, máximo 10) sube de 0 a 0.25 y a 0.5; desde 10 no sube más; al bajar de 0.25 sale del carrito. La papa (paso 1) sube de 1 en 1.
- **FE-C · Cliente de la API.** Un `POST` manda la cabecera `X-Yapa-CSRF` con el token de la sesión y la cookie (`credentials: 'include'`). Una respuesta 422 se convierte en un error con el `codigo` y el `mensaje` de la API.
- **FE-D · Rol.** `admin` abre el panel de operaciones; `admin_zona` puede abrir el panel de zona y la tienda; `vecino` abre la tienda.
- **FE-E · Total aproximado del carrito.** 5 kg de papa amarilla a 4.03, 10 de papa blanca a 1.23 y 10 de cebolla a 2.35 suman **55.95** aprox. con los precios redondeados que se ven; el servidor, con los precios sin redondear (4.032…), da un subtotal de S/ 56.00 y un total de S/ 61.00 con el envío. Por eso el carrito dice "aprox." y el total que vale es el de `POST /api/cotizar`.

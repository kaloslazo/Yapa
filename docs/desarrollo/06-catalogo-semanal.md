# Iteración 6 · Catálogo semanal del proveedor aliado (CUN-01)

## Requisito

Como administrador de Yapa, quiero publicar cada semana la lista de productos con los precios por tramo y el stock que nos garantiza cada proveedor aliado, para que los vecinos vean un precio máximo que no va a cambiar durante la semana.

## Decisiones del equipo que se aplican

- **C-12 (Carlos, 23/09):** la lista la dan los proveedores aliados, con precios por tramo y **cantidad máxima**. "Es la lista que ellos otorgan, por eso serían aliados": el proveedor la respeta.
- **C-11:** catálogo corto, **marca única** por producto, frescos en pasos fijos de kg.
- **C-01:** precio máximo garantizado. Si el precio pudiera cambiar a mitad de semana, esa promesa no se cumpliría.
- **RN-16 (Entregable 1):** solo el administrador publica precios.
- **Sugerencia de Carlos:** que los proveedores suban sus ofertas directamente queda como mejora futura; por ahora la carga el administrador.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-33 | El catálogo de un ciclo se publica **antes** de que el ciclo abra (antes del lunes 00:00). Una vez abierto, **no cambia**: ni precios ni tramos. Solo se puede **desactivar** un producto (por ejemplo, si el proveedor lo retira). | — |
| S-34 | Los tramos deben empezar en 0, tener cantidades mínimas crecientes y precios **estrictamente decrecientes** y positivos: más volumen nunca sube el precio. | — |
| S-35 | El stock reservado (RP-08) se lleva **por ciclo**. Lo reservado una semana no cuenta para la siguiente. *(Corrige la limitación anotada en la iteración 3.)* | — |
| S-36 | Un producto desactivado a mitad de semana no acepta pedidos nuevos, pero los pedidos ya registrados se mantienen y se liquidan normal. | — |
| S-37 | Si un ciclo no tiene catálogo publicado, se usa el catálogo base del piloto (compatibilidad con las iteraciones anteriores). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| CT-01 | Solo un administrador de Yapa publica o desactiva productos (RN-16). | `NOT_AUTHORIZED` |
| CT-02 | Cada producto viene de un proveedor aliado activo. | `SUPPLIER_NOT_ALLIED` |
| CT-03 | Tramos válidos según S-34. | `INVALID_TIERS` |
| CT-04 | La cantidad máxima es mayor que 0 y múltiplo del paso del producto. | `INVALID_STOCK` |
| CT-05 | Marca única: un producto aparece una sola vez en el catálogo del ciclo. | `DUPLICATE_PRODUCT` |
| CT-06 | La categoría es `FRESCOS` o `LIMPIEZA` (las que tienen comisión definida). | `INVALID_CATEGORY` |
| CT-07 | Publicar es **todo o nada**: si un producto falla, no se publica ninguno. | el del producto que falla |
| CT-08 | Se puede publicar o reemplazar el catálogo solo antes de que el ciclo abra (S-33). | `CATALOG_LOCKED` |
| CT-09 | Desactivar un producto: solo el administrador, con un producto que exista en el catálogo del ciclo (S-36). | `NOT_AUTHORIZED`, `PRODUCT_NOT_AVAILABLE` |
| CT-10 | El registro, la cotización, el stock y la liquidación usan el catálogo **del ciclo del pedido** (S-35, S-37). | — |

## Criterios de aceptación

Catálogo de prueba para el ciclo 2026-W39 (abre el lunes 21/09): papa amarilla del proveedor aliado de frescos con tramos 0 → S/ 3.50, 100 → S/ 3.30; máximo 300 kg.

- **CT-A · Publicar.** El administrador publica el sábado 19/09 → el lunes 21/09 un vecino cotiza papa amarilla a S/ 3.92 (3.50 × 1.12), no al precio del catálogo base (S/ 4.032). → CT-10
- **CT-B · No administrador.** Un vecino intenta publicar → `NOT_AUTHORIZED`. → CT-01
- **CT-C · Proveedor no aliado.** → `SUPPLIER_NOT_ALLIED`. → CT-02
- **CT-D · Tramos inválidos.** Un primer tramo que no empieza en 0, un precio que sube con el volumen o un precio 0 → `INVALID_TIERS`. → CT-03
- **CT-E · Stock inválido.** Máximo 0, o 10.5 kg con paso de 1 kg → `INVALID_STOCK`. → CT-04
- **CT-F · Producto repetido.** → `DUPLICATE_PRODUCT`. → CT-05
- **CT-G · Categoría inválida.** `ABARROTES` → `INVALID_CATEGORY`. → CT-06
- **CT-H · Todo o nada.** Un catálogo con un producto válido y uno inválido → error, y el ciclo sigue sin catálogo publicado. → CT-07
- **CT-I · Precio fijo en la semana.** Intentar publicar para W39 el martes 22/09 → `CATALOG_LOCKED`. → CT-08
- **CT-J · Desactivar a mitad de semana.** Con un pedido de papa amarilla ya registrado, el administrador la desactiva → un pedido nuevo con papa recibe `PRODUCT_NOT_AVAILABLE`, y el pedido anterior se liquida normal. → CT-09, S-36
- **CT-K · Stock por ciclo.** 395 kg reservados en W38 no impiden pedir 6 kg en W39. → S-35
- **CT-L · Liquidación con los tramos del ciclo.** En W39, con 200 kg pedidos entre todos (tramo desde 100), el precio final es 3.30 × 1.12 = S/ 3.696. → CT-10

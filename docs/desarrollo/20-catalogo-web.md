# Iteración 20 · Publicar el catálogo semanal desde la web

## Requisito

Como administrador de Yapa, quiero cargar cada semana la lista de precios del proveedor aliado **desde la web** y desactivar un producto si el proveedor lo retira, sin tener que tocar código.

## Por qué

La iteración 6 dejó las reglas del catálogo (`publish_catalog`, `deactivate_product`), pero solo se podían usar desde el código o las pruebas. En la operación real, cada semana llega una lista nueva. Sin esta pantalla, el piloto no puede cambiar precios.

## Decisiones que se aplican

- **C-12:** la lista la dan los proveedores aliados, con precios por tramo y cantidad máxima.
- **Iteración 6 (CT-01..CT-09):** todas sus reglas se aplican igual; esta iteración solo agrega la forma de cargarlas.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-116 | La lista se pega como **texto separado por comas** (se puede copiar desde Excel o Google Sheets), una línea por producto: `codigo,nombre,categoria,unidad,paso,maximo,proveedor,desde1,precio1[,desde2,precio2...]`. Los decimales llevan punto. Se ignoran las líneas vacías y la línea de títulos que empieza con `codigo`. | — |
| S-117 | La pantalla abre con el ciclo **siguiente** y con el cuadro de texto ya lleno con su catálogo actual (el publicado o, si no hay, el base). Así el admin solo cambia lo que cambió el proveedor. Solo se copian los productos activos. | — |
| S-118 | Si el ciclo usa el catálogo base y el admin desactiva un producto, se guarda una **copia** del catálogo base como catálogo de ese ciclo, con el producto desactivado. El catálogo base no cambia. *(Antes daba `PRODUCT_NOT_AVAILABLE`, y en el piloto no se podía retirar un producto en una semana sin catálogo publicado.)* | — |
| S-119 | Los productos del catálogo base del piloto quedan asignados a los proveedores aliados de ejemplo según su categoría: frescos a `SUP-FRESCOS` y limpieza a `SUP-LIMPIEZA`. Sin esto, el catálogo base copiado no se podría volver a publicar (CT-02). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| CW-01 | `GET /admin/catalogo` muestra el ciclo pedido (`?ciclo=`) o el siguiente, si está publicado o usa el base, sus productos con sus tramos, y el cuadro de texto lleno según S-117. | `INVALID_CYCLE` si el ciclo no es válido |
| CW-02 | `POST /admin/catalogo` lee la lista (S-116). Si una línea no tiene el formato, se rechaza **toda** la lista e indica el número de línea. | `INVALID_CATALOG_FORMAT` |
| CW-03 | Una lista bien escrita pasa por `publish_catalog`: se aplican CT-01..CT-08 (todo o nada, ciclo aún no abierto). | los de la iteración 6 |
| CW-04 | `POST /admin/catalogo/desactivar` desactiva un producto del ciclo (CT-09, S-118). | `PRODUCT_NOT_AVAILABLE` |
| CW-05 | Solo el administrador entra a estas páginas. | 403 (AC-05) |

Una línea tiene **formato inválido** si tiene menos de 9 columnas, si los tramos no vienen en pares, si falta el código o el nombre, o si el paso, el máximo, las cantidades o los precios no son números con punto decimal (por ejemplo, `3,50` o `tres`).

## Criterios de aceptación

Hora: sábado 19/09/2026 (ciclo 2026-W38). El siguiente ciclo es 2026-W39, que abre el lunes 21/09.

- **CW-A · Pantalla.** `GET /admin/catalogo` muestra "2026-W39", avisa que usa el catálogo base, y el cuadro de texto trae la línea `PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,400,SUP-FRESCOS,0,3.60,100,3.38,250,3.20`. El plátano de seda (desactivado) no aparece en el cuadro. → CW-01, S-117, S-119
- **CW-B · Publicar.** Se publica para W39 una lista con título y dos productos:
  ```
  codigo,nombre,categoria,unidad,paso,maximo,proveedor,desde1,precio1,desde2,precio2
  PAPA-AMARILLA,Papa amarilla,FRESCOS,kg,1,300,SUP-FRESCOS,0,3.50,100,3.30
  LIMPIATODO-GALON,Limpiatodo galón 3.8 L,LIMPIEZA,unidad,1,60,SUP-LIMPIEZA,0,7.90,12,6.90
  ```
  → 200 y el ciclo W39 tiene esos 2 productos. El lunes 21/09, el catálogo que ve el vecino muestra la papa amarilla a S/ 3.92 (3.50 × 1.12). → CW-02, CW-03
- **CW-C · Formato inválido.** La misma lista con `3,50` en lugar de `3.50` en la línea 2 → 422 `INVALID_CATALOG_FORMAT`, el mensaje dice "línea 2" y W39 sigue sin catálogo publicado. Lo mismo con una línea de 8 columnas. → CW-02
- **CW-D · Regla del catálogo.** Una lista cuyo segundo tramo **sube** de precio → 422 `INVALID_TIERS`, sin publicar nada. → CW-03, CT-03, CT-07
- **CW-E · Ciclo abierto.** El martes 22/09, publicar para W39 → 422 `CATALOG_LOCKED`. → CT-08
- **CW-F · Desactivar.** Con el catálogo de CW-B publicado, el martes 22/09 el admin desactiva la papa amarilla de W39 → 200, la papa queda inactiva y ya no aparece en el catálogo del vecino. → CW-04
- **CW-G · Desactivar en un ciclo con catálogo base.** El miércoles 16/09 (W38 usa el base), el admin desactiva el ajo → W38 tiene su propio catálogo con el ajo inactivo y los demás productos iguales; el catálogo base sigue con el ajo activo. → S-118
- **CW-H · Solo el admin.** Un vecino que abre `/admin/catalogo` recibe 403. → CW-05

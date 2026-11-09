# Yapa — CUS-01 Publicar el catálogo semanal

**Fuente de las reglas:** `api/docs/desarrollo/06-catalogo-semanal.md` (CT), `20-catalogo-web.md` (CW), `54-proveedores-y-transportistas.md` (PV) y `22-precio-referencia.md`. Decisiones C-11 y C-12.

## 0. Objetivo y frontera

Dejar publicado, antes de que abra el ciclo, el catálogo de la semana: productos con sus tramos de precio por volumen y la cantidad máxima que el proveedor aliado puede vender. De ahí sale el precio máximo que ve el vecino (CUS-02) y el precio final de la liquidación (CUS-04).

Actores: **administrador de Yapa** (publica, aprueba y desactiva) y **proveedor aliado** (propone su lista desde su cuenta). El vecino solo consume el catálogo.

## 1. Requerimientos funcionales

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-01.1 | El administrador publica el catálogo de un ciclo pegando la lista del proveedor (texto separado por comas). | CT-01, CW-02, S-116 | Una línea mal escrita rechaza toda la lista e indica el número de línea (`INVALID_CATALOG_FORMAT`). |
| RF-01.2 | Cada producto viene de un proveedor aliado, con categoría `FRESCOS` o `LIMPIEZA`, sin repetirse. | CT-02, CT-05, CT-06 | `SUPPLIER_NOT_ALLIED`, `DUPLICATE_PRODUCT`, `INVALID_CATEGORY`. |
| RF-01.3 | Los tramos empiezan en 0, con mínimos crecientes y precios estrictamente decrecientes. | CT-03, S-34 | Un precio que sube con el volumen → `INVALID_TIERS`. |
| RF-01.4 | La cantidad máxima y el paso son mayores que 0 y la máxima es múltiplo del paso. | CT-04, S-120 | Máximo 0 o paso 0 → `INVALID_STOCK`. |
| RF-01.5 | Publicar es todo o nada y solo antes de que el ciclo abra. | CT-07, CT-08, S-33 | Publicar el martes para la misma semana → `CATALOG_LOCKED`. |
| RF-01.6 | El administrador puede desactivar un producto a mitad de semana; los pedidos ya hechos se mantienen. | CT-09, S-36, S-118 | Un pedido nuevo con ese producto → `PRODUCT_NOT_AVAILABLE`; el anterior se liquida normal. |
| RF-01.7 | El proveedor propone su lista para un ciclo que no abrió; el administrador la aprueba o la rechaza con motivo. | PV-01..PV-05, RN-16 | La propuesta no cambia el catálogo hasta aprobarse; al aprobarse reemplaza solo los productos de ese proveedor. |
| RF-01.8 | El administrador registra precios de referencia del mercado y del supermercado, con fuente y fecha, vigentes 14 días. | iteración 22 | El vecino los ve en el catálogo solo mientras estén vigentes. |

## 2. Ficha

| Campo | Descripción |
|---|---|
| Identificador | CUS-01 |
| Actor principal | Administrador de Yapa |
| Actor secundario | Proveedor aliado |
| Disparador | El proveedor entrega su lista semanal (por su cuenta o por mensaje). |
| Precondiciones | Sesión de administrador; proveedor aliado registrado; el ciclo destino todavía no abrió. |
| Postcondición de éxito | El ciclo tiene su catálogo propio; las cotizaciones, los pedidos y la liquidación lo usan (CT-10). |
| Garantía ante fallo | Si un producto falla, no se publica ninguno y el ciclo queda como estaba. |

## 3. Flujo principal (publicar desde el panel)

| Paso | Administrador | Sistema |
|---|---|---|
| 1 | Abre "Catálogo" en el panel. | Muestra el ciclo siguiente, si usa el catálogo base o uno publicado, y el cuadro de texto lleno con la lista actual (S-117). |
| 2 | Pega o corrige la lista del proveedor. | — |
| 3 | Publica. | Lee la lista, valida cada producto (proveedor → tramos → stock → repetido → categoría, S-38) y la fecha. |
| 4 | — | Guarda el catálogo del ciclo de una sola vez y confirma. |

### Subflujo: propuesta del proveedor

| Paso | Actor | Sistema |
|---|---|---|
| 1 | El proveedor envía su lista desde su cuenta. | Valida formato, reglas del catálogo y que todos los productos sean suyos (PV-03). Queda `PENDIENTE`. |
| 2 | El administrador abre "Propuestas" y la aprueba. | Publica: reemplaza solo los productos de ese proveedor (S-286), todo o nada. |
| 2a | El administrador la rechaza con motivo. | Queda `RECHAZADA`; el proveedor ve el motivo y puede reenviarla. |

## 4. Flujos alternativos y excepciones

| Código | Condición | Respuesta |
|---|---|---|
| FA-01 | Formato inválido en una línea. | `INVALID_CATALOG_FORMAT` con el número de línea; no se publica nada. |
| FA-02 | Regla del catálogo violada (tramos, stock, categoría, proveedor, repetido). | El código de la regla; no se publica nada. |
| FA-03 | El ciclo ya abrió. | `CATALOG_LOCKED`; solo se puede desactivar productos. |
| FA-04 | El proveedor incluye un producto de otro proveedor. | `FOREIGN_SUPPLIER` o `FOREIGN_PRODUCT`. |
| FA-05 | Rechazo sin motivo. | `REASON_REQUIRED`. |
| EX-01 | Alguien que no es administrador intenta publicar o aprobar. | `NOT_AUTHORIZED` / 403. |

## 5. Escenarios de aceptación

1. **Publicar.** Se publica la W39 el sábado 19/09 → el lunes la papa amarilla se cotiza a S/ 3,92 (3,50 × 1,12). (CT-A)
2. **Ciclo abierto.** Publicar la W39 el martes 22/09 → `CATALOG_LOCKED`. (CT-I, CW-E)
3. **Todo o nada.** Una lista con un producto válido y uno con tramos que suben → `INVALID_TIERS` y el ciclo sigue sin catálogo. (CT-H, CW-D)
4. **Desactivar.** Con un pedido de papa registrado, se desactiva la papa → un pedido nuevo con papa da `PRODUCT_NOT_AVAILABLE`; el anterior se liquida normal. (CT-J)
5. **Propuesta.** El proveedor propone su lista; al aprobarla, sus productos se reemplazan y los de otros proveedores no cambian. (PV-F)

## 6. Pantallas y código

- Web: panel del administrador → Catálogo y Propuestas; panel del proveedor (`PartnerPanel.tsx`).
- API: `/api/admin/catalogo`, `/api/admin/catalogo/desactivar`, `/api/admin/propuestas/*`, `/api/proveedor/propuestas`, `/api/admin/referencias`.
- Motor: `catalog.py` (`publish_catalog`, `deactivate_product`, `parse_catalog`), `supplier_offers.py`, `reference.py`.

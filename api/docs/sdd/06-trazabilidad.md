# Matriz de trazabilidad · iteración 2

Cada fila une el origen de negocio, la regla, el criterio, el código y la prueba que lo verifica. Las rutas son `archivo:línea` del commit final de la iteración.

## Registrar pedido (CUN-02)

| Origen | Regla | Criterio | Código | Prueba |
|---|---|---|---|---|
| CUN-02 precondición, RN-22 | RP-01 | CA-02 | `order_registration.py:41` `_customer` | `test_ca02_*` |
| RN-01, C-07 | RP-02 | CA-03 | `order_registration.py:50` `_zone` | `test_ca03_*` |
| RN-02, S-02 | RP-03 | CA-04 | `cycle.py:24` `is_open` · `order_registration.py:57` | `test_ca04_*` (4 casos de frontera) |
| S-03 | RP-04 | CA-05 | `order_registration.py:157` · `store.py:35` `find_order` | `test_ca05_rejects_second_order_in_cycle` |
| RN-07 | RP-05 | CA-06, CA-07 | `order_registration.py:72` `_merge_lines` | `test_ca06_*`, `test_ca07_*` |
| RN-05, RN-07 | RP-06 | CA-08 | `order_registration.py:82` `_product` | `test_ca08_*` |
| C-11, S-08 | RP-07 | CA-09 | `order_registration.py:62` `_to_quantity` · `:90` `_check_quantity` | `test_ca09_*` (3 pruebas) |
| C-12 | RP-08 | CA-10 | `order_registration.py:100` `_check_stock` | `test_ca10_*` |
| C-01, RN-16 | RP-09 | CA-01, CA-13 | `domain.py:55` `max_unit_price` · `order_registration.py:113` | `test_ca01_*`, `test_ca13_*` |
| RN-03, S-04 | RP-10 | CA-11 | `order_registration.py:116` | `test_ca11_*` |
| C-09, S-09 | RP-11 | CA-01, CA-15 | `order_registration.py:122` · `domain.py:26` `floor_cents` | `test_ca01_*`, `test_ca15_*` |
| C-03 | RP-12 | CA-12 | `order_registration.py:127` | `test_ca12_rejects_payment_method_not_allowed`, `test_plin_is_allowed` |
| C-04, RN-12 | RP-13 | CA-12 | `order_registration.py:130` | `test_ca12_requires_operation_code`, `test_ca12_rejects_reused_operation_code` |
| C-04 | RP-14 | CA-12 | `order_registration.py:138` | `test_ca12_rejects_amount_*`, `test_ca12_rejects_non_numeric_amount` |
| CUN-03 (límite) | RP-15 | CA-14 | `order_registration.py:181` `verify_payment` | `test_ca14_*` |

## Liquidación ("te devolvemos")

| Origen | Regla | Criterio | Código | Prueba |
|---|---|---|---|---|
| C-03 | LQ-01 | CL-01 | `settlement.py:80` | `test_cl01_*` |
| C-06, C-07, S-06 | LQ-02 | CL-02, CL-03 | `settlement.py:89` | `test_cl02_*`, `test_cl03_*` |
| C-08, C-12 | LQ-03, LQ-04 | CL-04, CL-05 | `settlement.py:107` · `domain.py:59` `tier_for` | `test_cl04_*`, `test_cl05_*` |
| C-09 | LQ-05 | CL-06 | `settlement.py:120` | `test_cl06_*` (2 casos) |
| C-10 | LQ-06 | CL-07 | `settlement.py:58` `_missing_by_order` | `test_cl07_*` (4 casos) |
| C-01, C-05, S-09 | LQ-07, LQ-08 | CL-08 | `settlement.py:127` | `test_cl08_nobody_pays_more_than_shown` |
| C-02 | LQ-09 | CL-09 | `settlement.py:147` | `test_cl09_summary_is_transparent` |

## Recorrido para la defensa (una especificación de punta a punta)

**"Nunca pagarás más de lo que ves"** (C-01):

1. **Dónde está definida:** `10-clarificaciones-v2.md` (C-01, con el motivo legal: Ley 29571, art. 4.2) y `02-especificacion-cun-02.md` (RP-09, RP-11).
2. **Regla de negocio:** el precio máximo sale del catálogo, y el cobro se redondea a favor del cliente.
3. **Componente:** `Product.max_unit_price` (`domain.py:55`) y `quote_order` (`order_registration.py:106`). En la liquidación, `min(precio del tramo, precio máximo)` (`settlement.py`).
4. **Verificación:** `test_ca13_prices_come_from_catalog`, `test_cl08_nobody_pays_more_than_shown`, y en vivo `python -m yapa_sdd.cli ciclo ejemplos/ciclo_demo.json`.

**"¿Qué pasa cuando cambia una spec?"**

En esta iteración cambió la regla de cobro: RN-21 (saldo en la puerta) pasó a C-01/C-02 (precio máximo y liquidación). El historial de Git lo muestra en orden:

`docs: clarificaciones` → `docs: spec v2` → `docs: criterios` → `docs: plan` → `test: pruebas (rojo)` → `feat: registro` → `feat: liquidación`.

También hubo dos ajustes de spec **durante** la implementación (la cotización y el faltante de un pedido no entregado). Ambos entraron primero como `docs:` y después como `test:`, antes del código.

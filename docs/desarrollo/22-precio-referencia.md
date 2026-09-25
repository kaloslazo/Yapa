# Iteración 22 · Precio de referencia y ahorro frente al mercado

## Requisito

Como vecino, quiero ver cuánto cuesta el mismo producto en el mercado del barrio o en el supermercado, para saber si Yapa me conviene. Como Yapa, quiero medir cuánto ahorró de verdad cada canasta frente a esos precios, porque es la propuesta de valor.

## Por qué

- Hueco 2 de la iteración 8: "ahorro entregado" solo mide lo que vuelve por volumen y envío. No dice si el vecino pagó menos que en el mercado.
- El kit de campo (`kit-validacion-campo.md`) ya junta esos precios, pero quedan en un CSV y no llegan al sistema.
- **Ley 29571 (publicidad veraz):** una comparación de precios tiene que ser verdadera y comprobable. Por eso cada precio de referencia lleva su **fuente** y su **fecha**, y deja de mostrarse cuando está viejo.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-125 | El admin registra precios de referencia por producto, de dos tipos: `MERCADO` (mercado de barrio) y `SUPERMERCADO`. Cada precio lleva fuente (por ejemplo, "Mercado de Lince") y fecha en que se observó. Se usa el **más reciente por fecha** de cada producto y tipo. | — |
| S-126 | Un precio de referencia vale **14 días** desde que se observó. Pasado ese plazo ya no se muestra ni se usa en métricas. | 14 días |
| S-127 | El catálogo del vecino muestra los precios de referencia vigentes con su fuente y fecha, **aunque Yapa salga más caro**. Es lo transparente, y le avisa al equipo que ese producto no conviene. | — |
| S-128 | La meta de ahorro es **15 %** frente a la referencia (la misma del kit de campo). La pantalla del admin marca los productos que no llegan. | 15 % |
| S-129 | El ahorro real de un ciclo se mide por tipo de referencia y solo con canastas **comparables**: pedidos liquidados en los que cada producto recibido tiene un precio de ese tipo vigente al cierre del ciclo (a 14 días o menos, antes o después). Se compara **Σ precio de referencia × cantidad recibida** con el **monto final** que pagó el vecino, envío incluido (en el mercado no se paga envío). Los reclamos no se descuentan. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| RF-01 | Solo el admin registra precios de referencia. | `NOT_AUTHORIZED` |
| RF-02 | El producto existe en el catálogo base o en el del ciclo actual. | `PRODUCT_NOT_AVAILABLE` |
| RF-03 | El tipo es `MERCADO` o `SUPERMERCADO`. | `INVALID_REFERENCE_KIND` |
| RF-04 | El precio es mayor que 0; la fuente no está vacía; la fecha no es futura. | `INVALID_PRICE`, `SOURCE_REQUIRED`, `INVALID_DATE` |
| RF-05 | Para cada producto y tipo se usa el precio más reciente por fecha que siga vigente (S-125, S-126). | — |
| RF-06 | El catálogo del vecino muestra los vigentes con fuente y fecha (S-127). | — |
| RF-07 | `/admin/referencias`: formulario para registrar y tabla con el precio máximo de Yapa, las referencias vigentes y el ahorro en %, con aviso si es menor que 15 % (S-128). | — |
| RF-08 | `reference_savings(store, ciclo)` da, por tipo: canastas comparables, total de referencia, total Yapa, ahorro en soles y en %. Sin canastas comparables, no da porcentaje. Se muestra en `/admin/metricas`. | `CYCLE_NOT_SETTLED` si no está liquidado |

## Criterios de aceptación

Precios de ejemplo, observados el jueves 17/09/2026. Los del supermercado salen de la plantilla del kit. Los del mercado son **inventados para la prueba**, porque todavía no se hizo la visita de campo.

| Producto | Supermercado ("Plaza Vea online") | Mercado ("Mercado de Lince") |
|---|---|---|
| Papa amarilla (kg) | 7.99 | 4.50 |
| Papa blanca (kg) | 2.39 | 1.50 |
| Cebolla roja (kg) | 3.89 | 2.50 |

Canasta de prueba: 5 kg de papa amarilla, 10 kg de papa blanca y 10 kg de cebolla. Con 8 pedidos en Jesús María, el monto final es S/ 57.64 por pedido (iteración 2).

- **RF-A · Registrar.** El admin registra los 6 precios desde la web → quedan guardados con fuente, fecha y quién. → RF-01, RF-07
- **RF-B · El vecino los ve.** El viernes 18/09, el catálogo muestra en la papa amarilla "Mercado de Lince: S/ 4.50" y "Plaza Vea online: S/ 7.99", con la fecha 17/09. El viernes 02/10 (15 días después) ya no aparecen. → RF-06, S-126
- **RF-C · Datos inválidos.** Tipo `FERIA` → `INVALID_REFERENCE_KIND`; precio 0 → `INVALID_PRICE`; fuente vacía → `SOURCE_REQUIRED`; fecha 19/09 registrada el 18/09 → `INVALID_DATE`; producto `MANDARINA` → `PRODUCT_NOT_AVAILABLE`; un vecino → `NOT_AUTHORIZED` (y 403 en la web). → RF-01..RF-04
- **RF-D · El más reciente.** Después de los de 17/09, se registra papa amarilla en el mercado a S/ 4.80 con fecha 15/09 → sigue valiendo S/ 4.50 (es más reciente). → RF-05
- **RF-E · Ahorro del ciclo.** Se liquida W38 con los 8 pedidos:
  - frente al supermercado: 8 canastas, referencia S/ 822.00 (8 × 102.75), Yapa S/ 461.12 (8 × 57.64), ahorro **S/ 360.88 (43.9 %)**;
  - frente al mercado: 8 canastas, referencia S/ 500.00 (8 × 62.50), Yapa S/ 461.12, ahorro **S/ 38.88 (7.8 %)**.
  → RF-08, S-129
- **RF-F · Sin canasta completa.** Si la cebolla no tiene precio de mercado, frente al mercado hay 0 canastas comparables y no hay porcentaje. → S-129
- **RF-G · Pantalla del admin.** La papa amarilla muestra el precio máximo de Yapa S/ 4.03, ahorro frente al mercado 10.4 % con el aviso "menos de 15 %" y frente al supermercado 49.5 %. → RF-07, S-128
- **RF-H · Métricas en la web.** `/admin/metricas?ciclo=2026-W38` muestra "43.9 %" y "7.8 %". → RF-08

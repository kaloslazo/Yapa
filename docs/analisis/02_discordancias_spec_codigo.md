# 02 · Discordancias entre spec, código y tests (repo `sdd-2026-exposicion`)

Revisado el 23/09/2026 sobre el commit `bd48598`. La suite pasa (8/8, Python 3.12), pero pasar los tests no significa que el código cumpla la spec: los tests solo cubren el camino feliz y un error por regla.

Cada caso de abajo se **ejecutó** contra `register_weekly_order` (el script de prueba está al final).

## A. El código contradice o excede la spec

| # | Entrada | Resultado real | Problema | Regla |
|---|---|---|---|---|
| D1 | Ventana `SUN_09_12` (no existe) | `DELIVERY_WINDOW_FULL` | Una ventana inexistente se reporta como "llena". Falta un código `DELIVERY_WINDOW_INVALID`. | RN-09 |
| D2 | Dirección en Lince **no validada** | `ADDRESS_OUTSIDE_COVERAGE` | Mezcla dos causas distintas. Al cliente se le dice "fuera de cobertura" aunque viva en Lince. | RN-01 / RN-07 |
| D3 | Distrito `"Jesus Maria"` sin tildes | `ADDRESS_OUTSIDE_COVERAGE` | Se compara el texto exacto. La spec no define cómo normalizar, ni si la zona sale de la geocodificación (AN-04). | RN-01 |
| D4 | Carrito vacío / cantidad 0 / cantidad negativa | `PRODUCT_NOT_ACTIVE` | Tres errores distintos con el mismo código. Faltan `EMPTY_ORDER` e `INVALID_QUANTITY`. | RN-07 |
| D5 | 0.001 "unidad" de un producto | Aceptado | No hay granularidad por unidad de medida: los kg pueden tener decimales, las unidades no. La spec no dice nada. | RN-05 |
| D6 | Subtotal real 49.995 | Aceptado como 50.00 | **Se redondea antes de comparar con el mínimo.** La spec no define si el mínimo se aplica al valor exacto o al redondeado. | RN-03 |
| D7 | `now` = miércoles 20:00:00 exacto | Aceptado | "Hasta las 20:00": no está definido si el límite es inclusivo. Tampoco hay zona horaria (`America/Lima`); se usan datetimes naive. | RN-02 |
| D8 | Ciclo jueves–viernes pasado como parámetro | Aceptado | RN-02 fija "lunes 00:00 – miércoles 20:00", pero el código acepta cualquier inicio y cierre que le pasen. La regla no está en el código: está en quien llama a la función. | RN-02 |
| D9 | Pedido fuera de ciclo | `CYCLE_CLOSED` (rechazo) | **El negocio dice otra cosa**: RN-02 y CUN-02 EX-02 dicen que el pedido "pasa al siguiente ciclo", no que se rechaza. | RN-02 |
| D10 | Ventana llena **y** subtotal bajo | `DELIVERY_WINDOW_FULL` | No hay un orden definido para los errores. El plan (`03-plan.md`) valida líneas → subtotal → ventana → pago, pero el código valida zona → ciclo → ventana → pago → líneas. El plan y el código no coinciden. | — |
| D11 | Mismo producto en 2 líneas | Aceptado | No se definió si se consolidan o se rechazan las líneas duplicadas (afecta a CUN-04). | — |
| D12 | Mismo `order_id` dos veces | Aceptado | No hay idempotencia ni regla de "un pedido por cliente por ciclo". CUN-04 EX-02 menciona "duplicidad", pero CUN-02 no la previene. | — |
| D13 | Capacidad de ventana | Global | RN-09 dice "capacidad **por zona**", pero `DeliveryWindow` no tiene zona. | RN-09 |
| D14 | Reserva de cupo | No se descuenta | CUN-02 paso 7 dice "reserva el cupo". El código solo lee `reserved`, no lo incrementa, y no se considera la concurrencia (el último cupo pedido por dos clientes a la vez). | RN-09 |

## B. Cosas del CUN-02 del Entregable 1 que la spec omitió

- **Cliente suspendido (RN-22)**: un cliente con deuda no debería poder registrar pedidos, y no se valida. (El Entregable 1 tampoco lista RN-22 en CUN-02; la inconsistencia viene desde el modelado.)
- **Cliente identificado** (precondición de CUN-02): no aparece en la entrada.
- **Preferencia de sustitución** (paso 2 y EN-08 `preferenciaSustitución`): se capturaría en CUN-02 y se aplicaría en CUN-05/06. Se difirió RN-08 entera, cuando al menos habría que capturar la preferencia.
- **Monto faltante** (FA-01): el error del mínimo no dice cuánto falta.
- **Ahorro frente al supermercado** (sección 4.1, "registro mostrando... cuánto se estaría ahorrando"): no aparece.
- **Aceptación de condiciones** (paso 6): no aparece.
- **Total referencial vs. final (RN-21)**: la salida muestra `total` como si fuera definitivo. Debería marcarse como estimado/referencial.

## C. La spec deja entrar datos que no debería

- El JSON de entrada de `02-especificacion-cun-02.md` incluye `unitPrice`, `name` y `unit` **enviados por el cliente**. Según RN-05 y RN-16, el precio lo pone el catálogo publicado por el administrador. Tal como está escrito, el cliente fija su propio precio. El código sí toma el precio de `CatalogItem`, así que la spec y el código dicen cosas distintas.
- `addressValidated: true` también lo envía el cliente. Debería salir del sistema (la dirección guardada y geocodificada).

## D. Tests: qué verifican realmente

- 7 de 8 tests comprueban el **mensaje en español** con una regex (`"cobertura"`, `"mínimo"`...), no el **código de error**, que es el contrato de la spec. Si alguien cambia un mensaje, falla un test aunque el comportamiento sea correcto; si alguien cambia el código de error, ningún test lo detecta.
- No hay tests de frontera: subtotal 49.99 / 50.00 / 119.99 / 120.00, `now` igual a inicio o cierre, `reserved = capacity - 1`.
- `PRODUCT_NOT_ACTIVE` (producto inactivo) **no tiene ningún test**, aunque la matriz dice que RN-07 está cubierta (solo por el test del camino feliz).
- `PRICE_NOT_VALID` por unidad vacía no se prueba; solo por vencimiento.
- `verification-report.md` pone "Resultado esperado" en lugar de pegar la salida real de la ejecución.

## E. Evidencia de proceso SDD (la rúbrica lo mide)

- En el historial de Git, **la spec, el plan, las tareas, el código y los tests entraron en el mismo commit** (`1707499 Refocus repository on SDD Yapa vertical`). No hay evidencia de que la spec fuera antes que el código. El enunciado lo dice explícitamente: *"No se recomienda elaborar primero todo el código y posteriormente escribir las especificaciones para justificarlo"*.
- El historial muestra que el repo antes era otro proyecto (`focuslist`, `docs/specs/01-focuslist-spec.md`, un experimento con TDD). Un docente que revise `git log` lo va a ver.
- Todos los commits son de un solo autor (`rootskalos`). El criterio "Trabajo colaborativo" pide participación de todos.
- `docs/sources.md` expone rutas locales (`/Users/kalosroots/Downloads/...`).

## F. Nombres que no coinciden entre repos

| Entregable 1 (fuente) | `yapa-proyecto-completo` | Problema |
|---|---|---|
| CUN-05 **Abastecer** compra consolidada | "**Reponer** compra consolidada" | Cambia el sentido (reponer implica inventario, y Yapa no tiene). |
| TN-02 **Encargado** de compras | "**Responsable** de compras" | Nombre distinto para el mismo rol. |
| RN-08: se aplica la preferencia elegida (sustituir con diferencia máx. 10 % o retirar y devolver) | "ante una sustitución, el cliente acepta el cambio o recibe devolución" | **Cambia la regla**: el original decide por preferencia previa, la paráfrasis pide aceptación en el momento. Se pierde el tope del 10 %. |
| Segmento: hogares en departamento | "hogares **y pequeños compradores**" | Aparece un segmento nuevo que no se modeló. |
| RN-06 "variación máxima 5 %; total se ajusta al peso real" | "admite como máximo 5 %" | Se pierde el ajuste del total. |

## Script de verificación

```bash
cd sdd-2026-exposicion
PYTHONPATH=src python docs/analisis/probe_edge_cases.py
```

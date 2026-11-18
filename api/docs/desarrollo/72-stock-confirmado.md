# Iteración 72 · Stock confirmado por cargas

> **Reescrita el 18/11/2026** con el formato de las demás specs (la versión del 17/11 tenía las reglas en párrafos y los supuestos S-361..S-364 en un rango sin decir cuál era cuál). Las reglas y las pruebas son las mismas. Desde la iteración 76 el detector corre a pedido también aquí (S-373).

## Requisito (Aaron, 17/11/2026)

Como proveedor, quiero sumar a mi stock cada carga que tengo, con una foto y el conteo, para que la cantidad disponible de mi lista salga de lo que de verdad tengo.

## Alcance

El stock va aparte del catálogo publicado y de las reservas: solo llena la cantidad disponible del borrador de la lista. Publicar sigue pasando por la aprobación del equipo (PV-01..PV-03). No guarda la foto, solo su huella para no sumarla dos veces.

## Supuestos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-361 | El stock confirmado va aparte por proveedor y por la semana de su propuesta (la siguiente). Empieza en cero y solo suma cargas revisadas. La misma foto exacta no se suma dos veces. | — |
| S-362 | En lo que se vende por kg manda el peso medido; las unidades de la foto nunca se pasan a kilos. | peso > 0 y ≤ 100 000 kg |
| S-363 | Lo vendible se redondea hacia abajo al paso del producto (con paso 1 kg, 4.1 kg confirmados son 4 kg vendibles). | — |
| S-364 | El total vendible reemplaza la cantidad disponible del borrador de la lista; si la unidad del borrador es otra, se avisa y no se cambia. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| ST72-1 | `GET /api/proveedor/stock?ciclo=` da lo confirmado por producto: unidades, cantidad y vendible. | — |
| ST72-2 | `POST /api/proveedor/stock/confirmar` con `ciclo`, `conteo` y la foto suma la carga. Repetir la misma foto con el mismo conteo devuelve el mismo total con `repetida`; con otro conteo, error. | `STOCK_ALREADY_CONFIRMED` |
| ST72-3 | Entre 1 y 30 filas, solo productos activos del proveedor, unidades enteras de 1 a 300; se revisa toda la carga antes de guardar. | `INVALID_STOCK_ITEM` |
| ST72-4 | Producto por kg sin peso medido válido. | `WEIGHT_REQUIRED` |
| ST72-5 | Solo para la semana siguiente; foto JPG, PNG o WebP de hasta 8 MB. | `INVALID_STOCK_CYCLE`, `PHOTO_REQUIRED`, `PHOTO_TOO_LARGE`, `INVALID_PHOTO` |
| ST72-6 | Solo el proveedor con sesión. | `NOT_AUTHORIZED` / 401 |

## Criterios de aceptación

Escenario base: proveedores `stock-frescos` (SUP-FRESCOS) y `stock-limpieza` (SUP-LIMPIEZA); la semana de la propuesta es 2026-W39.

- **ST72-A · Suma y repetición.** Dos filas de papa amarilla (1.2 kg y 2.3 kg) dan 3.5 kg; la misma foto otra vez sigue en 3.5 con `repetida`. Otra foto con 0.6 kg deja 4.1 kg, 4 vendibles y 6 unidades. → ST72-2, S-361, S-363
- **ST72-B · Peso.** Zanahoria sin peso, `NaN`, `Infinity`, 0 o −1 dan `WEIGHT_REQUIRED` y no se guarda nada. → ST72-4, S-362
- **ST72-C · Producto de otro proveedor.** Ajo y limpiatodo en la misma carga de frescos dan `INVALID_STOCK_ITEM` y no se guarda nada. → ST72-3
- **ST72-D · Unidades y reinicio.** 3 galones de limpiatodo son 3 vendibles, también después de guardar y abrir la base. → ST72-1
- **ST72-E · Foto confirmada.** La misma foto con otro conteo da `STOCK_ALREADY_CONFIRMED`. → ST72-2
- **ST72-F · API.** Confirma 0.5 kg de ajo, repetir da `repetida` y el máximo del ajo en el catálogo no cambia; sin sesión, 401. → ST72-2, ST72-6, Alcance
- **ST72-G · Pantalla.** Sin peso no se confirma la fila; con 2.5 kg se confirma y el borrador recibe 2 vendibles; se ve "3 unidades visibles". → ST72-4, S-364
- **ST72-H · Precios por volumen.** Cada producto del editor trae sus precios por volumen en un desplegable cerrado.
- **ST72-I · Unidad distinta.** Con stock en kg y el borrador en unidades, el borrador no cambia y aparece el aviso "unidad distinta". → S-364

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| ST72-1, S-363 | `supplier_stock.snapshot`; `web/api.py` `proveedor_stock` | `test_stock72.test_st72_a_*`, `test_st72_d_*` |
| ST72-2, S-361 | `supplier_stock.confirm` (huella SHA-256 de la foto) | `test_st72_a_*`, `test_st72_e_*`, `test_st72_f_*` |
| ST72-3 | `supplier_stock._clean_rows` | `test_st72_c_*` |
| ST72-4, S-362 | `supplier_stock._weight` | `test_st72_b_*` |
| ST72-5 | `confirm` y `_check_photo` | sin prueba propia (es el mismo control de formato y tamaño que `vision.analyze_photo`) |
| ST72-6 | rutas solo para `proveedor` | `test_st72_f_*` |
| S-364, pantalla | `SupplierStock.tsx`, `SupplierListEditor.tsx`, `utils/supplierDraft.ts` | `stock72.test.ts` (ST72-G..I) |

## Evidencia

`72-stock-rojo.txt`, `72-stock-motor-verde.txt` y `72-stock-web-verde.txt` (17/11/2026, en la máquina de Aaron).

# Iteración 69 · La cotización del proveedor leída con IA

## Requisito

Como proveedor aliado, quiero mandar la foto de mi cotización (la pizarra, el cuaderno o la lista impresa) o pegar el mensaje que ya escribo por WhatsApp, y que Yapa llene mi lista con precios, tramos y cantidades, para no tipear producto por producto. Yo reviso y la envío como siempre.

## Por qué

La propuesta del curso pide "actualización de catálogo asistida: procesamiento de cotizaciones del mayorista (imágenes/listas) con IA para actualizar precios del catálogo rápidamente". Hasta la iteración 68 el proveedor llenaba cada campo a mano en el editor de la iteración 63.

## Alcance

Un paso de lectura antes del flujo de PV-01..PV-03: la IA solo llena el borrador del editor. Nada se guarda ni se publica hasta que el proveedor envía la lista y el equipo la aprueba (sin cambios en esas reglas).

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-345 | La foto se lee con un modelo de visión de Groq (plan gratuito; `YAPA_GROQ_MODELO_VISION`, por defecto `qwen/qwen3.8-27b`) y, de respaldo, GitHub Models (`openai/gpt-4o-mini`). El texto, con el modelo de siempre (S-314). | — |
| S-346 | Sin IA (sin clave o si falla), el texto se lee con reglas: cada renglón con el nombre de un producto del proveedor toma el primer precio (`S/ 3.40`, `a 3.40`) y la cantidad con unidad (`300 kg`, `20 u`); un renglón que empieza con "desde" agrega un tramo al producto anterior. La foto sin IA no se puede leer. | — |
| S-347 | Un producto que ya está en la lista del proveedor conserva su código, categoría, unidad y paso; si la cotización no trae cantidad, conserva el máximo actual. | — |
| S-348 | Un producto nuevo recibe un código hecho con su nombre (mayúsculas, sin tildes, guiones), categoría Frescos si se vende por kg y Limpieza si es por unidad, paso 1 y, si no trae cantidad, máximo 0 para que el proveedor lo complete. | — |
| S-349 | Se descartan, con aviso, las filas sin precio o con precio fuera de S/ 0.01..S/ 1000, y las que usan un código de otro proveedor. Los tramos se ordenan por "desde" y el primero empieza en 0. | — |
| S-350 | Hasta 20 lecturas por proveedor y por día de Lima (con IA o con reglas). | 20 |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| LP-01 | `POST /api/proveedor/lista/leer` con `texto` o `foto_archivo` devuelve `filas` (código, nombre, categoría, unidad, paso, máximo, tramos), `nuevos` (códigos que no estaban), `avisos` y `fuente` (`ia` o `reglas`). No guarda nada. | — |
| LP-02 | Sin texto ni foto. | `LIST_REQUIRED` |
| LP-03 | Foto sin IA activa. | `IA_DISABLED` |
| LP-04 | Foto que no es JPG, PNG ni WebP, o de más de 8 MB. | `INVALID_PHOTO`, `PHOTO_TOO_LARGE` |
| LP-05 | La IA falla: con texto, se lee con reglas y se avisa; con foto, se informa. | `IA_UNAVAILABLE` (solo foto) |
| LP-06 | Más de 20 lecturas en el día. | `IA_LIMIT` |
| LP-07 | Solo un proveedor aliado activo. | `NOT_AUTHORIZED` (403) |

## Criterios de aceptación

Escenario base: el proveedor de frescos tiene papa amarilla (máx. 400 kg), cebolla roja y limón en su lista.

- **LP-A · Foto con IA.** La IA devuelve papa amarilla a 3.40 con tramo desde 100 a 3.10 y 300 kg, y "Papa huayro" a 4.20 sin código: las filas traen PAPA-AMARILLA con 2 tramos, categoría FRESCOS y paso 1, y PAPA-HUAYRO como nuevo con máximo 0. `fuente` es `ia`. → LP-01, S-347, S-348
- **LP-B · Lo ajeno y lo inválido.** Una fila con LEJIA-GALON (de limpieza) y otra con precio 0 se descartan con 2 avisos. → S-349
- **LP-C · Máximo que no vino.** Cebolla roja sin cantidad conserva 300. → S-347
- **LP-D · Texto con reglas.** Sin IA, "Papa amarilla S/ 3.40 (hay 300 kg)" y "desde 100 kg a 3.10" dan PAPA-AMARILLA con máximo 300 y tramos 0→3.40 y 100→3.10; `fuente` `reglas`. → S-346
- **LP-E · IA caída con texto.** La IA falla y el mismo texto se lee con reglas, con un aviso. → LP-05
- **LP-F · Foto sin IA.** `IA_DISABLED`. Foto con IA caída: `IA_UNAVAILABLE`. → LP-03, LP-05
- **LP-G · Vacío y foto inválida.** Sin nada: `LIST_REQUIRED`. Un archivo de texto como foto: `INVALID_PHOTO`. → LP-02, LP-04
- **LP-H · Límite.** La lectura 21 del día: `IA_LIMIT`. → LP-06
- **LP-I · La foto va al modelo de visión.** El pedido a la IA lleva la imagen como `image_url` en base64 y el modelo de visión. → S-345
- **LP-J · Permiso.** El admin y un vecino reciben 403. → LP-07
- **LP-K · Pantalla.** En el editor, "Leer cotización con IA" llena el borrador: actualiza los productos existentes, agrega los nuevos y deja "Borrador con cambios sin enviar". → LP-01

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| LP-01 | `quote_reader.read_quote`; `web/api.py` `proveedor_lista_leer` y la ruta `/api/proveedor/lista/leer` | `test_lista_proveedor_ia_69.test_lp_a_*`, `test_lp_01_*` |
| LP-02 | `read_quote` (`LIST_REQUIRED`) | `test_lp_g_*` |
| LP-03 | `read_quote` (`IA_DISABLED`) | `test_lp_f_*` |
| LP-04 | `quote_reader._photo_type` | `test_lp_g_*` |
| LP-05 | `read_quote`: reglas con texto, `IA_UNAVAILABLE` con foto | `test_lp_e_*`, `test_lp_f_*` |
| LP-06 | `quote_reader._count_use` | `test_lp_h_*` |
| LP-07 | ruta solo para `partners.SUPPLIER`; `partners.active` en `read_quote` | `test_lp_j_*` |
| S-345 | `ia.Provider.vision_model`, `ia.AIClient.ask_json(image=...)`, `ia.from_env` (`YAPA_GROQ_MODELO_VISION`) | `test_lp_i_*` |
| S-346 | `quote_reader._by_rules` | `test_lp_d_*` |
| S-347, S-348, S-349 | `quote_reader._clean` y `code_for` | `test_lp_a_*`, `test_lp_b_*`, `test_lp_c_*` |
| LP-K | `QuoteReader` y `fill` en `SupplierListEditor.tsx`; estilos `.quote-reader*` | `src/components/cotizacionIa.test.ts` |

## Evidencia

- `69-motor-rojo.txt` y `69-web-rojo.txt`: fallan antes del código (no existía `quote_reader`; el editor no tenía el lector).
- `69-motor-verde.txt` y `69-web-verde.txt`: motor, TypeScript, web y build en verde.
- Prueba real con Groq (16/11/2026, plan gratuito): la foto de una cotización escrita (5 productos, uno nuevo y un tramo "desde 100 kg") se leyó en 1.8 s sin errores; un mensaje de WhatsApp con 4 productos, en 2.2 s. En la demo, el proveedor de frescos pegó un mensaje y el borrador quedó con "3 actualizados y 1 nuevo".

## Costo

Groq y GitHub Models tienen nivel gratuito; con 20 lecturas por proveedor al día (S-350) el uso queda muy por debajo de sus límites. Sin claves, el texto se sigue leyendo con reglas, sin costo.

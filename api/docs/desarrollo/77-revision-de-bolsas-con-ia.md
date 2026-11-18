# Iteración 77 · Revisar la bolsa con IA que conoce el pedido

## Requisito

Como armador, quiero que "Sugerir con el detector" me diga qué productos del pedido se ven en la foto de la bolsa y cuántas piezas, sin confundir la papa blanca con la amarilla ni inventar productos. Como proveedor, lo mismo para contar una carga.

## Por qué

El detector YOLO (iteración 63 y siguientes) solo conoce papa, cebolla, ajo y zanahoria: 8 de los 12 productos del catálogo no los puede ver, y no distingue las dos papas. Se armó un banco de 46 fotos con respuesta conocida (`api/tools/banco_bolsas.py`): las 16 fotos del catálogo solas y 30 montajes de 2 a 4 productos sobre fondo de bolsa. Cada foto trae un "pedido" con lo que se ve y 3 productos que no están, para que filtrar por pedido no alcance. Resultado en `docs/modelo-yolo/banco-18nov.md`:

| Detector local (YOLO) | Aciertos | Inventados | Faltantes | Papa sin elegir | Fotos perfectas | Precisión | Cobertura |
|---|---|---|---|---|---|---|---|
| A · como estaba antes de la 76 | 29 | 25 | 77 | 5 | 5 de 46 | 54 % | 27 % |
| B · como quedó en la 76 (filtrado por pedido) | 29 | 7 | 77 | 5 | 9 de 46 | 81 % | 27 % |

Precisión: de lo que sugiere, cuánto está de verdad en la foto. Cobertura: de lo que hay en la foto, cuánto encuentra. El filtro de la 76 quitó casi todo lo inventado, pero la cobertura no pasa de 27 % porque el modelo no conoce 8 de los 12 productos.

La visión con IA ya está en el proyecto (iteración 69, `ia.ask_json` con imagen) y cuesta USD 0 en el nivel gratuito de Groq. A la IA se le da la lista del pedido, así que solo puede responder con productos del pedido, y nombra cada uno por su código.

## Alcance

Solo cambia de dónde salen las sugerencias. La revisión sigue siendo opcional y la confirma una persona (iteración 76); nada cambia pesos, precios, pagos ni el catálogo. YOLO queda de respaldo cuando no hay IA.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-375 | En Armado, la foto se revisa con IA dándole la lista de productos del pedido (código y nombre). Solo cuentan los códigos de esa lista; lo que la IA nombre fuera de ella se muestra aparte como "También se ve", sin código. | — |
| S-376 | En Stock del proveedor, la lista que recibe la IA son los productos de ese proveedor para la semana que viene. | — |
| S-377 | Si no hay IA configurada, si falla o si se pasó el límite del día, se usa el detector local (YOLO) como antes; si tampoco está, se revisa a mano. La respuesta dice de dónde salió ("Con IA" o "Con el detector local"). | — |
| S-378 | Hasta 150 revisiones con IA por cuenta y día de Lima. El nivel gratuito de Groq deja unas 7000 fichas por minuto y cada foto gasta unas 1000 a 2000: la pantalla achica la foto a 1024 px de lado antes de enviarla. | 150 por día |
| S-379 | La foto de la bolsa sale a Groq solo para leerla, como la cotización de la iteración 69. Puede tener el rótulo (número de pedido y edificio), no el nombre del vecino. No se guarda allá ni aquí: la foto que queda es la de la bolsa ya registrada. | — |
| S-380 | Las unidades que diga la IA son piezas o envases que se ven, de 1 a 300; nunca kilos (como S-358). Si no da un número válido, se pone 1 y el armador lo corrige. | 1..300 |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| VB-01 | `POST /api/vision/analizar` con la foto y `pedido` (armado) o `para=stock` (proveedor) devuelve `fuente` (`ia` o `detector`), `productos` con `codigo`, `nombre` y `cantidad`, y `otros`. Sin `pedido` ni `para`, responde como antes (solo detector local). | — |
| VB-02 | Con IA, solo se devuelven códigos de la lista (pedido o productos del proveedor), sin repetir. | — |
| VB-03 | Sin IA, con falla o pasado el límite: detector local, con `fuente: detector`. | `VISION_UNAVAILABLE` si tampoco hay detector |
| VB-04 | El pedido no existe. | `ORDER_NOT_FOUND` |
| VB-05 | Hasta 150 revisiones con IA por cuenta y día; después, detector local sin llamar a la IA. | — |
| VB-06 | Solo admin, armador y proveedor (como la iteración 63). | 401 / 403 |
| VB-07 | En pantalla, la fila llega con el producto ya elegido cuando hay `codigo`; se ve "Con IA" o "Con el detector local" y, si hay `otros`, "También se ve: …". La foto se achica a 1024 px antes de enviarla. | — |

## Criterios de aceptación

Escenario base: un pedido de Residencial San Felipe con papa amarilla, papa blanca y cebolla roja.

- **VB-A · IA con el pedido.** La IA responde `PAPA-BLANCA ×3` y `CEBOLLA-ROJA ×2`: llegan con `codigo`, `nombre` y `cantidad`, y `fuente: ia`. → VB-01, S-375
- **VB-B · Solo códigos del pedido.** Si la IA responde `LIMON ×2` (no está en el pedido), `INVENTADO ×1` y `PAPA-BLANCA` dos veces, solo queda una `PAPA-BLANCA`; `otros` trae lo que la IA puso aparte. → VB-02
- **VB-C · Lo que se manda a la IA.** El mensaje lleva los códigos y nombres de las líneas del pedido y la foto como imagen; no lleva el nombre del vecino. → S-375, S-379
- **VB-D · Sin IA.** Sin IA configurada, responde el detector local con `fuente: detector`. → VB-03, S-377
- **VB-E · IA caída.** Si los dos proveedores de IA fallan, responde el detector local. → VB-03
- **VB-F · Límite.** La revisión 151 del día no llama a la IA y usa el detector local. → VB-05, S-378
- **VB-G · Proveedor.** Con `para=stock`, la lista son sus productos de la semana que viene; un código de otro proveedor no pasa. → S-376
- **VB-H · Pedido que no existe.** `pedido = 999999` → `ORDER_NOT_FOUND`. → VB-04
- **VB-I · Unidades.** `"unidades": "muchas"` o 0 se vuelven 1; 500 se vuelve 300. → S-380
- **VB-J · Pantalla.** Con dos papas en el pedido y la respuesta `PAPA-BLANCA ×3` con código, la fila llega con Papa blanca elegida; se ve "Con IA" y "También se ve: tomate". El formulario lleva `pedido`. → VB-07

## Trazabilidad

(se completa al terminar)

## Evidencia

- `77-motor-rojo.txt` y `77-web-rojo.txt`: las pruebas fallan antes del código.
- `77-motor-verde.txt` y `77-web-verde.txt`: motor, TypeScript, web y build en verde.
- `docs/modelo-yolo/banco-18nov.md`: el banco y la medición.

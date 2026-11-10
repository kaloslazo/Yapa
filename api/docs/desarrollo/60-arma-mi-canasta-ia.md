# Iteración 60 · "Arma mi canasta" con IA (Groq, con GitHub Models de respaldo)

## Requisito

Como vecino, quiero escribir con mis palabras qué voy a cocinar en la semana (por ejemplo, "somos 4 y haré lomo saltado y ají de gallina") y recibir una canasta sugerida con productos del catálogo de esa semana, para agregarla a mi canasta con un toque.

## Por qué

Kalos lo pidió el 09/11/2026 y eligió proveedores gratis.

- **Groq** es el principal: unas 1 000 consultas al día sin tarjeta.
- **GitHub Models** es el respaldo: 150 consultas al día con la cuenta de GitHub del equipo.

Los dos usan el formato de "chat completions" de OpenAI, así que el mismo código sirve para ambos.

La propuesta de chatbot (`propuesta-chatbot.md`) ya decía que la IA solo aporta donde hay texto libre. Por eso la IA **sugiere** y el motor sigue decidiendo con sus reglas de siempre: precio, pasos, tope y mínimo.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-314 | **Proveedores.** Principal: Groq (`https://api.groq.com/openai/v1/chat/completions`), con la clave `YAPA_GROQ_CLAVE` y el modelo `YAPA_GROQ_MODELO` (por defecto `openai/gpt-oss-120b`). Respaldo: GitHub Models (`https://models.github.ai/inference/chat/completions`), con `YAPA_GITHUB_MODELS_CLAVE` y `YAPA_GITHUB_MODELS_MODELO` (por defecto `openai/gpt-4o-mini`). Cada llamada espera hasta 15 s. Si el principal falla (error, límite, tiempo o respuesta que no es JSON), se prueba el respaldo. Sin ninguna clave, la función está apagada. | Groq + GitHub Models |
| S-315 | El vecino escribe de 3 a 300 caracteres. Hay un máximo de **10 sugerencias por vecino al día** (hora de Lima), para cuidar el cupo gratis. | 10 al día |
| S-316 | Al modelo solo se le manda el catálogo del ciclo (código, nombre, unidad, paso, tope por línea y precio máximo) y el texto del vecino. **Ningún dato personal.** | — |
| S-317 | **La respuesta se limpia.** Solo quedan productos activos del catálogo del ciclo. Cada cantidad se redondea hacia arriba a su paso, entre un paso y el tope por línea. Los productos repetidos se suman. Se aceptan hasta 12 productos. El precio y el subtotal los calcula el motor (precio máximo, RP-09). Si el subtotal no llega a S/ 50, se dice cuánto falta, sin completar la canasta por su cuenta. La sugerencia no reserva stock ni crea el pedido: el vecino la agrega a su canasta y sigue el flujo normal (RP-01..RP-14). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| IA-01 | Sin clave de ningún proveedor, la función está apagada: `/api/estado` dice `ia: false` y pedir una sugerencia da error. | `IA_DISABLED` |
| IA-02 | Solo un vecino con sesión. El texto tiene de 3 a 300 caracteres. | `INVALID_INPUT` |
| IA-03 | Hasta 10 sugerencias por vecino al día (S-315). | `IA_LIMIT` |
| IA-04 | Se usa el principal y, si falla, el respaldo. Si fallan los dos, se responde con error. | `IA_UNAVAILABLE` |
| IA-05 | La respuesta se limpia según S-317. Si no queda ningún producto, se responde con error. | `IA_EMPTY_SUGGESTION` |
| IA-06 | La sugerencia trae las líneas con nombre, cantidad, precio máximo y total; además el subtotal, lo que falta para el mínimo, un comentario corto del modelo (hasta 200 caracteres) y qué proveedor respondió. | — |
| IA-07 | Al modelo solo se le manda el catálogo y el texto (S-316). | — |

## Criterios de aceptación

En las pruebas se usa un modelo falso: ninguna prueba sale a internet. Catálogo base de W38.

- **IA-A · Sugerencia.** El modelo responde `{"lineas":[{"id":"PAPA-AMARILLA","cantidad":2.4},{"id":"CEBOLLA-ROJA","cantidad":3},{"id":"NO-EXISTE","cantidad":1},{"id":"PAPA-AMARILLA","cantidad":1}],"comentario":"Para 4 personas"}`. Quedan papa amarilla 4 kg (2,4 + 1 = 3,4, redondeado a 4) y cebolla roja 3 kg, con el precio máximo del catálogo. Lo que falta para S/ 50 es exacto, el comentario es "Para 4 personas" y el proveedor es "groq". → IA-05, IA-06, S-317
- **IA-B · Tope.** Pedir 25 kg de papa deja 10 kg (tope por línea, S-08). → S-317
- **IA-C · Respaldo.** Si Groq responde con error 429, responde GitHub Models y el proveedor es "github". Si los dos fallan → `IA_UNAVAILABLE`. Si Groq responde algo que no es JSON, se usa el respaldo. → IA-04
- **IA-D · Sin productos válidos.** Si todo lo que propone el modelo está fuera del catálogo → `IA_EMPTY_SUGGESTION`. → IA-05
- **IA-E · Límites.** Un texto de 2 o de 301 caracteres → `INVALID_INPUT`. La consulta número 11 del día → `IA_LIMIT`; al día siguiente vuelve a funcionar. → IA-02, IA-03
- **IA-F · Apagada.** Sin claves, `/api/estado` trae `ia: false` y `POST /api/canasta/sugerir` responde `IA_DISABLED`. → IA-01
- **IA-G · Sin datos personales.** El mensaje que recibe el modelo no contiene el nombre, el celular ni el correo del vecino. → IA-07
- **IA-H · Configuración.** Con `YAPA_GROQ_CLAVE` y `YAPA_GITHUB_MODELS_CLAVE` hay dos proveedores, en ese orden. Solo con la de GitHub hay uno. Sin ninguna, no hay IA. → S-314

# Iteración 70 · Asistente de compra en "¿Te ayudamos?"

## Requisito

Como vecino, quiero preguntarle a Yapa en el chat cómo va mi pedido, cuánto ahorré, cuánto cuesta un producto, cuándo llega y si mi edificio ya llegó al mínimo, y que me responda con mis datos, sin esperar al equipo.

## Por qué

La propuesta del curso pide un "asistente de compra (chatbot): chat con IA para que el usuario consulte estado de pedido, precios, ahorro estimado y ventana de entrega sin intervención del equipo". La ayuda de la iteración de Aaron solo busca en las preguntas frecuentes.

## Alcance

Lectura: el asistente no cambia pedidos, pagos ni saldo. Para cuidar el costo, las cinco consultas frecuentes se responden con reglas sobre los datos del motor (sin IA) y solo lo demás va a Groq, con un contexto corto y un límite por día.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-351 | Temas que se responden sin IA, por palabras de la pregunta (sin tildes): `pedido` (estado del pedido de la semana o el último), `entrega` (día de entrega y cierre), `ahorro` (lo devuelto en el último pedido liquidado y el saldo), `precio` (precio máximo y hasta dónde puede bajar, con el súper si hay referencia) y `grupo` (pedidos verificados del grupo frente a 8). | — |
| S-352 | Lo demás va a la IA con un contexto de solo ese vecino: su nombre, la semana, su pedido, su último ahorro, su saldo, el avance de su grupo y los precios de la semana. Nunca datos de otros vecinos. Respuesta de hasta 400 tokens. | — |
| S-353 | Hasta 10 preguntas con IA por vecino y por día de Lima; las respuestas con datos no cuentan. Pasado el límite, o sin IA, se responde con sugerencias de lo que sí se puede preguntar. | 10 |
| S-354 | Sin sesión de vecino, el chat sigue mostrando las preguntas frecuentes y pide entrar para consultar el pedido. | — |
| S-355 | El contexto de la IA incluye un resumen de las reglas de Yapa (pago por Yape o Plin por adelantado, cierre del miércoles, mínimo de 8 por grupo, entrega el sábado, el ahorro vuelve como saldo y los reclamos dentro de 24 horas con foto). Con modelos `openai/gpt-oss-*`, el pedido va con `reasoning_effort: low`: si razonan mucho se quedan sin tokens para responder (visto en la prueba real del 16/11/2026). | — |
| S-356 | "El último pedido liquidado" es el de la semana más reciente, no el de número más alto. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AS-01 | `POST /api/asistente` con `pregunta` devuelve `respuesta`, `tema`, `fuente` (`datos`, `ia` o `sin_respuesta`) y `sugerencias`. | — |
| AS-02 | Pregunta vacía. Se recorta a 300 caracteres. | `QUESTION_REQUIRED` |
| AS-03 | Los temas de S-351 se responden con datos, sin llamar a la IA. | — |
| AS-04 | Lo demás se responde con IA y el contexto de S-352. | — |
| AS-05 | Sin IA, si falla o pasado el límite: `sin_respuesta` con sugerencias (no es un error). | — |
| AS-06 | Solo un vecino con sesión. | `NOT_AUTHORIZED` (403) |

## Criterios de aceptación

Escenario base: 8 pedidos verificados de Residencial San Felipe, miércoles 16/09/2026 10:00 (semana abierta). El vecino es el del primer pedido.

- **AS-A · Pedido.** "¿Dónde está mi pedido?" → tema `pedido`, fuente `datos`, menciona el número del pedido. → AS-03
- **AS-B · Precio.** "¿Cuánto cuesta la papa amarilla?" → tema `precio`, menciona "Papa amarilla" y "S/". → AS-03
- **AS-C · Ahorro.** "¿Cuánto ahorré?" → tema `ahorro`, menciona el saldo. → AS-03
- **AS-D · Grupo.** "¿Cuántos faltan para el mínimo?" → tema `grupo`, dice "8 de 8". → AS-03
- **AS-E · Entrega.** "¿Cuándo llega?" → tema `entrega`, menciona el sábado 19/09. → AS-03
- **AS-F · IA con contexto propio.** "¿Me conviene pedir más limón?" va a la IA; el contexto trae su nombre y no el de otro vecino; fuente `ia`. → AS-04, S-352
- **AS-G · Sin IA.** La misma pregunta sin IA → `sin_respuesta` con sugerencias. → AS-05
- **AS-H · Límite.** La pregunta 11 con IA del día no llama a la IA y responde `sin_respuesta`; las de datos siguen. → S-353
- **AS-I · Vacía.** `QUESTION_REQUIRED`. → AS-02
- **AS-J · Permiso.** El admin recibe 403. → AS-06
- **AS-L · Último ahorro.** Con un pedido liquidado en la semana 38 y otro (de número mayor) en la 37, "¿Cuánto ahorré?" habla del de la 38. → S-356
- **AS-M · Razonamiento bajo y reglas.** Con el modelo `openai/gpt-oss-120b`, el pedido a la IA lleva `reasoning_effort: low` y el contexto trae "Yape o Plin". → S-355
- **AS-K · Pantalla.** Con sesión, el chat manda lo que se escribe al asistente y muestra la respuesta como burbuja; sin sesión (401), muestra las preguntas frecuentes y el aviso para entrar. → S-354

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| AS-01 | `assistant.answer`; `web/api.py` `asistente` y la ruta `/api/asistente` | `test_asistente_70.test_as_a_*` |
| AS-02 | `answer` (`QUESTION_REQUIRED`, recorte a 300) | `test_as_i_*` |
| AS-03, S-351 | `assistant.TOPICS`, `_topic` y `_by_data` | `test_as_a_*` .. `test_as_e_*` |
| AS-04, S-352 | `assistant.context` y `answer` (`ask_json` con `max_tokens=400`) | `test_as_f_*` |
| AS-05, S-353 | `_use_ai` y la respuesta `sin_respuesta` | `test_as_g_*`, `test_as_h_*` |
| AS-06 | ruta solo para `vecino` | `test_as_j_*` |
| AS-K, S-354 | `FaqChatbot.tsx` (`askAssistant`, burbujas con "Con tus datos" o "Con IA") | `src/components/asistente.test.ts` |

## Evidencia

- `70-motor-rojo.txt` y `70-web-rojo.txt`: las pruebas fallan antes del código.
- `70-motor-verde.txt` y `70-web-verde.txt`: motor, TypeScript, web y build en verde.

## Costo

Las cinco consultas frecuentes no llaman a la IA. Las demás usan el nivel gratuito de Groq con un contexto de un solo vecino, respuestas de hasta 400 tokens y 10 por vecino al día.

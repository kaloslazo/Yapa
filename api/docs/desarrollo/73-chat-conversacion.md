# Iteración 73 · El chat como conversación: preguntas, opciones y última respuesta

> **Reescrita el 18/11/2026** con el formato de las demás specs. Las reglas y las pruebas son las mismas. El 18/11 también se juntó el tema y las palabras extra de cada pregunta frecuente con la pregunta (`data/faqs.ts`): estaban en dos listas aparte por posición y una pregunta 11 habría roto el chat.

## Requisito (Aaron, 17/11/2026)

Como vecino, quiero escribir mi duda en "¿Te ayudamos?" y ver mi pregunta, opciones parecidas y la respuesta al final de la conversación, sin que el chat llame a la IA para lo que ya está en las preguntas frecuentes.

## Alcance

Solo pantalla. Se conserva el asistente de la iteración 70 (`/api/asistente`) para lo personal y para lo que el vecino quiera consultar. No agrega servicios ni claves.

## Supuestos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-365 | Lo que no es personal se busca primero en las preguntas frecuentes, sin IA. Si no hay coincidencias, el chat lo dice y ofrece "Consultar asistente de compra"; solo con ese toque va al asistente (que puede usar IA, iteración 70). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| CH73-1 | Enviar una duda muestra la pregunta del vecino y opciones de las preguntas frecuentes; elegir una agrega su respuesta. No llama a la API. | — |
| CH73-2 | Las preguntas personales (pedido, entrega, ahorro, precio, grupo) van a `/api/asistente` como en la 70, con su rótulo "Con tus datos" o "Con IA". | — |
| CH73-3 | La respuesta nueva queda al final de la conversación y a la vista. | — |
| CH73-4 | "Reiniciar" borra la conversación y descarta las respuestas que estaban en camino. Escape cierra y devuelve el foco al botón. | — |

## Criterios de aceptación

- **CH73-A · Opciones sin IA.** "pagué" muestra la pregunta en la conversación y opciones; elegir "¿Cómo pago mi pedido?" agrega la respuesta con "Yape o Plin" al final. No hay llamadas a la API. → CH73-1, CH73-3
- **CH73-B · Duda desconocida.** "astronauta galaxia" responde "No encontré una respuesta segura" y ofrece "Consultar asistente de compra"; no llama a la API. → S-365
- **CH73-C · Reiniciar.** Con "¿Dónde está mi pedido?" en camino, reiniciar y luego recibir la respuesta deja la conversación vacía. → CH73-4

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| CH73-1, S-365 | `FaqChatbot.tsx` (`askQuestion` sin `forceAssistant`) y `utils/faqSearch.ts` | `chat73.test.ts` (CH73-A, CH73-B), `faqSearch.test.ts` |
| CH73-2 | `FaqChatbot.tsx` (`personal`, `askQuestion`) | `asistente.test.ts` (AS-K) |
| CH73-3 | efecto que baja la conversación y `data-chat-bottom` | `chat73.test.ts` (CH73-A) |
| CH73-4 | `generation` en `FaqChatbot.tsx` | `chat73.test.ts` (CH73-C), `FaqChatbot.test.ts` |

## Evidencia

`73-chat-rojo.txt`, `73-chat-motor-verde.txt` y `73-chat-web-verde.txt` (17/11/2026, en la máquina de Aaron).

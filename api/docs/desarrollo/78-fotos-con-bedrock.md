# Iteración 78 · Las fotos se leen con Claude en Bedrock (cuenta estudiantil)

## Requisito

Como equipo, queremos que la revisión de bolsas y la lectura de cotizaciones por foto no se corten por el cupo gratuito de Groq, usando el Bedrock de la cuenta estudiantil de AWS (UTEC), la misma donde corre el servidor.

## Por qué

Al medir la iteración 77 con el banco de 46 fotos, el nivel gratuito de Groq para su modelo de visión cortó dos veces:

- **Por minuto**: unas 7000 fichas, 2 o 3 fotos por minuto entre todos.
- **Por día**: 200 000 fichas, unas 80 fotos al día, compartidas con las demás funciones con IA. Se agotó en plena medición: 13 de 46 fotos quedaron sin respuesta.

Cuando eso pasa, la app cae al detector local (YOLO), que encuentra el 27 % de lo que hay en la foto. La cuenta estudiantil tiene Bedrock con créditos y en la misma región del servidor (Ohio, `us-east-2`) responden Claude Haiku 4.5, Claude Sonnet 4.6 y los Nova; los Claude 5.x aparecen en la lista pero la cuenta no tiene acceso. Resultado de Claude Haiku 4.5 en el mismo banco: `docs/modelo-yolo/banco-18nov.md`.

## Alcance

Solo cambia quién lee las fotos. Las reglas de la 69 (cotización) y de la 77 (bolsas) no cambian. Lo que es solo texto (asistente, Arma mi canasta, atención) sigue con Groq. El motor sigue sin dependencias: la firma de AWS (SigV4) se hace con la biblioteca estándar.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-381 | Con Bedrock configurado, las fotos (bolsas y cotizaciones) van primero a Bedrock; si falla, a Groq y a GitHub Models como hoy; para bolsas, al final el detector local. El texto no pasa por Bedrock. | — |
| S-382 | El modelo es Claude Haiku 4.5 por el perfil de inferencia de EE. UU. (`us.anthropic.claude-haiku-4-5-20251001-v1:0`), en `us-east-2`. Se puede cambiar con `YAPA_BEDROCK_MODELO`. | Haiku 4.5 |
| S-383 | Las credenciales son de un usuario IAM de la cuenta UTEC que solo puede invocar ese modelo, en variables propias (`YAPA_BEDROCK_CLAVE_ID`, `YAPA_BEDROCK_CLAVE_SECRETA`), nunca las variables `AWS_*` del sistema, para no usar por error otra cuenta. | — |
| S-384 | Si se define `YAPA_BEDROCK_CUENTA`, antes de la primera foto el motor pregunta a AWS de qué cuenta son las credenciales; si no es esa, no usa Bedrock (sigue con Groq) hasta reiniciar. | 434415659695 |
| S-385 | Cada foto va con máximo 400 fichas de respuesta para bolsas y 2000 para cotizaciones (Bedrock reserva cupo según ese máximo). | 400 / 2000 |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| BR-01 | Con `YAPA_BEDROCK_CLAVE_ID` y `YAPA_BEDROCK_CLAVE_SECRETA`, la IA tiene a Bedrock primero para fotos; sin ellas, todo queda como antes. | — |
| BR-02 | La llamada usa la API Converse de `bedrock-runtime` (`POST /model/{modelo}/converse`), con la foto como bytes, el mensaje del sistema y el máximo de fichas, firmada con SigV4 (`bedrock`, la región configurada). | — |
| BR-03 | Si Bedrock responde con error (permiso, límite, tiempo) o sin JSON, se pasa al siguiente proveedor. | — |
| BR-04 | Una pregunta sin foto nunca va a Bedrock. | — |
| BR-05 | Con `YAPA_BEDROCK_CUENTA`, si STS dice otra cuenta, Bedrock queda apagado. | — |

## Criterios de aceptación

- **BR-A · Orden.** Con Bedrock, Groq y GitHub configurados, una foto va primero a Bedrock y la respuesta de Bedrock es la que se usa. → BR-01, S-381
- **BR-B · Sin foto, sin Bedrock.** Una pregunta de texto va directo a Groq; Bedrock no recibe nada. → BR-04
- **BR-C · Lo que se manda.** La URL es `https://bedrock-runtime.us-east-2.amazonaws.com/model/us.anthropic.claude-haiku-4-5-20251001-v1%3A0/converse`; el cuerpo trae `system`, la foto en `image.source.bytes` (base64) con su formato y `inferenceConfig.maxTokens`; la cabecera `Authorization` es `AWS4-HMAC-SHA256` con el alcance `{fecha}/us-east-2/bedrock/aws4_request`. → BR-02, S-382
- **BR-D · Firma.** La firma reproduce el ejemplo publicado por AWS para SigV4 (GET de IAM `ListUsers`, 30/08/2015). → BR-02
- **BR-E · Bedrock caído.** Si Bedrock da 403 o 429, responde Groq. → BR-03
- **BR-F · Cuenta equivocada.** Con `YAPA_BEDROCK_CUENTA=434415659695` y STS diciendo `111111111111`, la foto va a Groq y Bedrock no se vuelve a llamar. Con la cuenta correcta, se pregunta a STS una sola vez. → BR-05, S-384
- **BR-G · Variables propias.** Con solo `AWS_ACCESS_KEY_ID` y `AWS_SECRET_ACCESS_KEY` en el entorno, no hay Bedrock. → S-383
- **BR-H · Bolsa con Bedrock.** En la API de la 77, con Bedrock como único proveedor, la revisión de una bolsa responde con `fuente: ia` y los códigos del pedido. → S-381

## Trazabilidad

(se completa al terminar)

## Evidencia

- `78-motor-rojo.txt`: las pruebas fallan antes del código.
- `78-motor-verde.txt` y `78-web-verde.txt`: motor, TypeScript, web y build en verde.
- `docs/modelo-yolo/banco-18nov.md`: Claude Haiku 4.5 por Bedrock en el banco de 46 fotos, con la cuenta UTEC.

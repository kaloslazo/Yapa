# Iteración 78 · Las fotos se leen con Bedrock de la cuenta estudiantil

## Requisito

Como equipo, queremos que la revisión de bolsas y la lectura de cotizaciones por foto no se corten por el cupo gratuito de Groq, usando el Bedrock de la cuenta estudiantil de AWS (UTEC), la misma donde corre el servidor.

## Por qué

Al medir la iteración 77 con el banco de 46 fotos, el nivel gratuito de Groq para su modelo de visión cortó dos veces:

- **Por minuto**: unas 7000 fichas, 2 o 3 fotos por minuto entre todos.
- **Por día**: 200 000 fichas, unas 80 fotos al día, compartidas con las demás funciones con IA. Se agotó en plena medición: 13 de 46 fotos quedaron sin respuesta.

Cuando eso pasa, la app cae al detector local (YOLO), que encuentra el 27 % de lo que hay en la foto. La cuenta estudiantil tiene Bedrock con créditos en la misma región del servidor (Ohio, `us-east-2`). Los Claude 5.x aparecen en la lista pero la cuenta no tiene acceso, y para los Claude 4.x Bedrock pide antes un formulario de caso de uso de Anthropic que la cuenta todavía no envió. Los Nova de Amazon responden sin formulario.

Medición en el banco (`docs/modelo-yolo/banco-18nov.md`), en las 46 fotos:

| | Precisión | Cobertura | Fotos perfectas |
|---|---|---|---|
| YOLO filtrado (76) | 81 % | 27 % | 9 de 46 |
| Nova 2 Lite | 97 % | 72 % | 28 de 46 |
| **Nova Pro** | **95 %** | **94 %** | **38 de 46** |

En las 33 fotos que Groq alcanzó a responder, Groq saca 98 % y 98 % y Nova Pro 95 % y 95 %: casi lo mismo, sin cortes.

## Alcance

Solo cambia quién lee las fotos. Las reglas de la 69 (cotización) y de la 77 (bolsas) no cambian. Lo que es solo texto (asistente, Arma mi canasta, atención) sigue con Groq. El motor sigue sin dependencias: la firma de AWS (SigV4) se hace con la biblioteca estándar.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-381 | Con Bedrock configurado, las fotos (bolsas y cotizaciones) van primero a Bedrock; si falla, a Groq y a GitHub Models como hoy; para bolsas, al final el detector local. El texto no pasa por Bedrock. | — |
| S-382 | El modelo es Amazon Nova Pro por el perfil de inferencia de EE. UU. (`us.amazon.nova-pro-v1:0`), en `us-east-2`: el mejor medido entre los que la cuenta puede usar hoy. Se cambia con `YAPA_BEDROCK_MODELO`; cuando se envíe el formulario de Anthropic, se mide Claude Haiku 4.5 (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) con el mismo banco y se usa si sale mejor. | Nova Pro |
| S-383 | Las credenciales son de un usuario IAM de la cuenta UTEC que solo puede invocar ese modelo, en variables propias (`YAPA_BEDROCK_CLAVE_ID`, `YAPA_BEDROCK_CLAVE_SECRETA`), nunca las variables `AWS_*` del sistema, para no usar por error otra cuenta. | — |
| S-384 | Si se define `YAPA_BEDROCK_CUENTA`, antes de la primera foto el motor pregunta a AWS de qué cuenta son las credenciales; si no es esa, no usa Bedrock (sigue con Groq) hasta reiniciar. | 434415659695 |
| S-385 | Cada foto va con máximo 400 fichas de respuesta para bolsas y 2000 para cotizaciones (Bedrock reserva cupo según ese máximo). | 400 / 2000 |
| S-386 | Si el modelo responde el JSON entre marcas de código (```json ... ```), se toma el objeto de adentro, como ya hace `ia._json_object`. | — |

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
- **BR-C · Lo que se manda.** La URL es `https://bedrock-runtime.us-east-2.amazonaws.com/model/us.amazon.nova-pro-v1%3A0/converse`; el cuerpo trae `system`, la foto en `image.source.bytes` (base64) con su formato y `inferenceConfig.maxTokens`; la cabecera `Authorization` es `AWS4-HMAC-SHA256` con el alcance `{fecha}/us-east-2/bedrock/aws4_request`. → BR-02, S-382
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

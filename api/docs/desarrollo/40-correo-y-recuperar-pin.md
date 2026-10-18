# Iteración 40 · Correo obligatorio y recuperar el PIN con un código

## Requisito

Como vecino, quiero recuperar mi PIN yo solo con un código que me llega a mi correo, sin esperar a que alguien del equipo me escriba. Como Yapa, quiero tener el celular y el correo de cada vecino, y que el correo solo sirva para recuperar la cuenta cuando se comprobó que es del vecino.

## Por qué

Decisión del equipo (18/10/2026): el correo y el celular son obligatorios, y la recuperación no puede depender de una persona (la cola manual de la iteración 39 no escala). Se quiere permitir también "Entrar con Google" (iteración 41). Esta iteración deja lista la base: el correo del vecino, su verificación y el código.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-201 | **Correo obligatorio en el alta**, además del celular. Es único por vecino sin importar mayúsculas. El consentimiento del vecino pasa a cubrir nombre, celular y correo (Ley 29733). | — |
| S-202 | **Un correo solo sirve para recuperar cuando está verificado**: se comprobó con un código enviado a ese correo. Así un error al escribirlo no entrega la cuenta a un desconocido. | — |
| S-203 | **Código de 6 dígitos**, vale 10 minutos, 5 intentos, y se puede pedir otro cada 60 segundos, hasta 5 por hora por vecino. | 10 min, 5 intentos, 60 s, 5 por hora |
| S-204 | Quien tiene correo verificado recupera su PIN solo: código más un PIN nuevo que elige. Quien no lo tiene entra en la cola del equipo (iteración 39). | — |
| S-205 | La respuesta de "Olvidé mi PIN" es siempre la misma, y los errores del código también (no se revela quién está registrado ni qué tiene verificado). | — |
| S-206 | Los vecinos que ya existen sin correo siguen entrando con su PIN; al entrar la app les pide agregar y verificar su correo. | — |
| S-207 | Los códigos no se guardan en claro (solo un resumen). Un PIN nuevo reemplaza al anterior y quita el bloqueo de la cuenta. | — |
| S-208 | El correo sale de una cuenta de Yapa con contraseña de aplicación, guardada en variables de entorno (nunca en el código ni en el repositorio). Sin esas variables, el motor imprime el código en su consola: solo para desarrollo y demo. | — |
| S-209 | Un código de recuperación no se manda si ya se mandó uno hace menos de 60 s o si ya van 5 en la última hora: en silencio, con la misma respuesta (evita que alguien llene de correos a un vecino ajeno). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| CR-01 | El alta pide `correo`: con formato `texto@dominio.ext`, sin espacios, máximo 120 caracteres, único sin importar mayúsculas. Se guarda en minúsculas y sin verificar. | `EMAIL_REQUIRED`, `INVALID_EMAIL`, `EMAIL_ALREADY_REGISTERED` |
| CR-02 | `POST /api/cuenta/correo` (vecino con sesión): guarda o cambia el correo con las reglas de CR-01, lo deja sin verificar y manda un código de verificación. | `LOGIN_REQUIRED`, `FORBIDDEN`, las de CR-01, `EMAIL_CODE_TOO_SOON`, `EMAIL_CODE_LIMIT`, `EMAIL_SEND_FAILED` |
| CR-03 | `POST /api/cuenta/correo/verificar {codigo}`: si el código es bueno, el correo queda verificado. | `INVALID_CODE` |
| CR-04 | El código tiene 6 dígitos, vale 10 minutos y se agota a los 5 intentos fallidos. Un código nuevo reemplaza al anterior. | `INVALID_CODE` |
| CR-05 | `POST /api/pin/olvide`: con correo verificado manda un código de recuperación a ese correo; sin correo verificado crea la solicitud para el equipo (OP-02). La respuesta es siempre la misma y los límites de S-209 se aplican en silencio. | `INVALID_INPUT` |
| CR-06 | `POST /api/pin/restablecer {usuario, codigo, pin}`: con un código bueno cambia el PIN (6 dígitos), quita el bloqueo, gasta el código y cierra las solicitudes de PIN abiertas de ese vecino. Cualquier fallo (número que no existe, sin correo verificado, código malo o vencido) da el mismo error. | `INVALID_CODE`, `INVALID_PIN` |
| CR-07 | Ni la sesión ni ninguna respuesta incluyen un código; en el repositorio solo hay su resumen. | — |
| CR-08 | `GET /api/sesion` del vecino agrega `correo` (enmascarado, por ejemplo `a***@gmail.com`) y `correo_verificado`. | — |
| CR-09 | El envío usa un correo inyectable. Si falla en una ruta anónima, la respuesta no cambia; en una ruta con sesión da `EMAIL_SEND_FAILED`. | `EMAIL_SEND_FAILED` |
| CR-10 | En pantalla: el alta pide el correo; "¿Olvidaste tu PIN?" tiene el paso "Ya tengo mi código" (código y PIN nuevo); la cuenta muestra "Verifica tu correo" si falta, con los campos de correo y código. | — |

## Criterios de aceptación (`tests/test_cuenta_correo.py`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| CR-A | Alta sin correo | alta sin `correo` | `EMAIL_REQUIRED` |
| CR-B | Formato | `ana@`, `a b@x.com`, 121 caracteres | `INVALID_EMAIL` |
| CR-C | Único | el mismo correo con otras mayúsculas | `EMAIL_ALREADY_REGISTERED` |
| CR-D | Se guarda en minúsculas y sin verificar | `Ana@Gmail.com` | guardado `ana@gmail.com`, sin verificar |
| CR-E | Agregar correo con sesión | vecino 101 manda su correo | se envía un código de 6 dígitos a ese correo |
| CR-F | Verificar | el código recibido | `GET /api/sesion` dice `correo_verificado` verdadero y el correo enmascarado |
| CR-G | Código malo | código equivocado | `INVALID_CODE` y sigue sin verificar |
| CR-H | Se agota | 5 intentos malos y luego el bueno | `INVALID_CODE` |
| CR-I | Vence | el bueno a los 11 minutos | `INVALID_CODE` |
| CR-J | Reenvío muy pronto | segundo pedido a los 30 s | `EMAIL_CODE_TOO_SOON` |
| CR-K | Tope por hora | sexto pedido en una hora (con 60 s entre cada uno) | `EMAIL_CODE_LIMIT` |
| CR-L | Olvidé con correo verificado | número de 101 verificado | misma respuesta de siempre y un correo con código; sin solicitud para el equipo |
| CR-M | Olvidé sin correo verificado | número de 101 sin verificar | misma respuesta, ningún correo y una solicitud para el equipo |
| CR-N | Número que no existe | `987654` | misma respuesta, ningún correo ni solicitud |
| CR-O | Restablecer | código bueno y PIN `135790` | 200; entra con `135790`; el PIN anterior ya no sirve |
| CR-P | Quita el bloqueo | cuenta bloqueada por intentos | tras restablecer puede entrar |
| CR-Q | El código se gasta | usar el mismo código dos veces | la segunda da `INVALID_CODE` |
| CR-R | Errores iguales | número que no existe, sin correo verificado y código malo | todos `INVALID_CODE` con el mismo mensaje |
| CR-S | PIN inválido | código bueno y PIN `12` | `INVALID_PIN` y el código sigue valiendo |
| CR-T | Cierra la cola | había solicitud abierta | tras restablecer, la lista del equipo queda vacía |
| CR-U | Sin código en claro | revisar el repositorio y las respuestas | el código no aparece |
| CR-V | Falla el envío | el correo falla en `olvide` | misma respuesta; en `cuenta/correo` da `EMAIL_SEND_FAILED` |
| CR-W | Roles | sin sesión o admin en `cuenta/correo` | `LOGIN_REQUIRED` o `FORBIDDEN` |
| CR-Y | Cambiar el correo | un vecino con correo verificado pone otro | queda sin verificar y "Olvidé mi PIN" va a la cola del equipo |
| CR-Z | Se guarda y se carga | verificar el correo, pedir un código, guardar la base y cargarla | el correo sigue verificado y el código pedido sigue sirviendo |
| CR-X | Envío en consola | sin credenciales | el código se imprime en el aviso del motor |

Las reglas de pantalla (CR-10) se verifican en el navegador.

## Trazabilidad

Se completa al terminar la implementación.

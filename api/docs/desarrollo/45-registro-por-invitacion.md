# Iteración 45 · Registro por invitación

## Requisito

Como vecino nuevo, quiero entrar a Yapa desde un enlace que me manda un vecino (por ejemplo por WhatsApp), registrarme con mi correo o con Google y quedar de una vez en su zona, sin esperar a que alguien me dé de alta. Como admin de zona, quiero tener mi enlace para invitar a mi edificio y ver que se vaya llenando mi grupo. Como equipo, queremos que el registro siga siendo **solo por invitación**, para no abrir las zonas a cualquiera.

## Por qué

Hoy un vecino solo existe si el admin lo da de alta a mano (nombre, celular, zona, consentimiento), y "Entrar con Google" solo sirve para quien ya tiene cuenta. Eso frena el crecimiento: cada vecino nuevo depende de una persona. El código de referido (`ANA101`) ya existe, pero solo se usa en el alta manual, y se puede adivinar (nombre más número), así que no sirve como llave de entrada.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-236 | **El registro propio es solo por invitación.** Sin un enlace de invitación válido no se puede crear una cuenta. El alta manual del admin sigue igual. | solo con enlace |
| S-237 | **Cada vecino tiene su propio enlace de invitación**, con un código **al azar** (no el código de referido, que se puede adivinar). Un vecino puede **renovar** su enlace: el anterior deja de valer y el nuevo entra en su lugar. | enlace propio y renovable |
| S-238 | **Quien se registra entra a la zona de quien lo invitó** y queda como referido suyo, así que le toca el premio por referido de siempre (S-163: S/ 3.00 y S/ 3.00 cuando el primer pedido del nuevo queda liquidado). | misma zona y referido |
| S-239 | **Topes contra abuso**: cada enlace admite hasta **20 registros en 24 horas**, y el sistema guarda como máximo **200 registros a medio hacer** (código pedido y no confirmado); los que vencen se descartan. | 20 por día, 200 pendientes |
| S-240 | **Registro con correo**: el vecino escribe nombre, celular, correo y acepta el tratamiento de datos; Yapa le manda un código de 6 dígitos (las mismas reglas de la iteración 40) y, al confirmarlo, el vecino **elige su PIN** y entra. **Registro con Google**: Google da el nombre y el correo (ya verificado); el vecino solo pone celular y acepta el tratamiento de datos; la cuenta nace **sin PIN** y entra con Google (puede crear un PIN después con "Olvidé mi PIN", que usa su correo verificado). | correo o Google |
| S-241 | **Datos obligatorios**: nombre, celular de 9 dígitos que empieza con 9 y no está repetido, correo que no está repetido, y consentimiento (Ley 29733). **El celular no se verifica por SMS** (costaría dinero). | como el alta del admin |
| S-242 | **Avisos**: cuando alguien se registra con un enlace, quien lo invitó y el admin de esa zona (si es otra persona) reciben un aviso **dentro de la app** ("Lucía se unió con tu enlace"). No sale por correo. | aviso en la app |
| S-243 | Un vecino **suspendido** no puede invitar: su enlace deja de valer mientras dure la suspensión. | sin enlace si está suspendido |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| IN-01 | `GET /api/mi-invitacion` (vecino con sesión) devuelve su enlace activo (lo crea la primera vez) y cuántas personas se registraron con él (hoy y en total). | `LOGIN_REQUIRED`, `FORBIDDEN` |
| IN-02 | `POST /api/mi-invitacion/renovar` (vecino con sesión) invalida el enlace anterior y da uno nuevo (S-237). | `LOGIN_REQUIRED`, `FORBIDDEN` |
| IN-03 | `GET /api/invitaciones/{código}` (sin sesión) devuelve la zona, el distrito, el **primer nombre** de quien invita y cuántos vecinos tiene la zona. No devuelve celular, correo, dirección ni apellido. Un código que no existe, que se renovó o de un vecino suspendido da el mismo error. | `INVITE_NOT_FOUND` |
| IN-04 | `POST /api/invitaciones/{código}/correo` (sin sesión) con `nombre`, `celular`, `correo`, `consentimiento` valida los datos (S-241), respeta el tope de S-239 y las reglas de código de la iteración 40, guarda el registro **a medio hacer** y manda el código al correo. No crea cuenta todavía. | `INVITE_NOT_FOUND`, `INVITE_LIMIT`, `NAME_REQUIRED`, `INVALID_PHONE`, `PHONE_ALREADY_REGISTERED`, `INVALID_EMAIL`, `EMAIL_ALREADY_REGISTERED`, `CONSENT_REQUIRED`, `EMAIL_CODE_TOO_SOON`, `EMAIL_CODE_LIMIT`, `EMAIL_SEND_FAILED`, `SIGNUPS_FULL` |
| IN-05 | `POST /api/invitaciones/{código}/confirmar` (sin sesión) con `correo`, `codigo` y `pin` revisa el código (vence a los 10 minutos, 5 intentos) y el PIN (6 dígitos, no obvio); si todo está bien **crea el vecino** en la zona de quien invitó con su correo ya verificado y su PIN, lo deja como referido (S-238) y abre su sesión. Cualquier fallo del código da el mismo error. | `INVITE_NOT_FOUND`, `INVALID_CODE`, `INVALID_PIN`, `PHONE_ALREADY_REGISTERED`, `EMAIL_ALREADY_REGISTERED` |
| IN-06 | `POST /api/invitaciones/{código}/google` (sin sesión) con `credential` (el token de Google), `celular` y `consentimiento` verifica el token (iteración 41), toma de él el nombre y el correo verificado, crea el vecino **sin PIN** con la cuenta de Google vinculada, y abre su sesión (S-240). | `INVITE_NOT_FOUND`, `INVITE_LIMIT`, `GOOGLE_NOT_CONFIGURED`, `INVALID_GOOGLE_TOKEN`, `INVALID_PHONE`, `PHONE_ALREADY_REGISTERED`, `EMAIL_ALREADY_REGISTERED`, `GOOGLE_ALREADY_LINKED`, `CONSENT_REQUIRED` |
| IN-07 | Cada registro completado cuenta contra el tope del enlace (S-239) y manda los avisos de S-242. | — |
| IN-08 | El alta manual del admin y el código de referido de siempre siguen funcionando igual. La sesión del vecino nuevo es igual a la de quien entra con PIN. | — |

## Criterios de aceptación (`tests/test_invitaciones.py`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| IN-A | Mi enlace | el vecino 101 pide `GET /api/mi-invitacion` dos veces | el mismo código las dos veces, de al menos 8 caracteres, distinto de `ANA101` |
| IN-B | Renovar | `POST /api/mi-invitacion/renovar` | código nuevo; con el anterior, `INVITE_NOT_FOUND` |
| IN-C | Vista previa | `GET /api/invitaciones/{código}` sin sesión | zona de Ana, primer nombre `Ana`, sin apellido, sin celular ni correo; con un código inventado, `INVITE_NOT_FOUND` |
| IN-D | Suspendido | el vecino 101 suspendido | su enlace da `INVITE_NOT_FOUND` |
| IN-E | Registro con correo | datos válidos, luego código y PIN `739104` | el vecino existe en la zona de Ana, `referred_by` es 101, correo verificado, entra con ese PIN; la sesión creada permite `GET /api/sesion` |
| IN-F | Validaciones | celular `812345678`, celular repetido, correo repetido, sin consentimiento, sin nombre | `INVALID_PHONE`, `PHONE_ALREADY_REGISTERED`, `EMAIL_ALREADY_REGISTERED`, `CONSENT_REQUIRED`, `NAME_REQUIRED`; no se manda correo ni se crea nada |
| IN-G | Código malo | código equivocado 5 veces | `INVALID_CODE` y el sexto intento con el código bueno también falla |
| IN-H | PIN flojo | PIN `123456` | `INVALID_PIN` y el código **no** se gasta (se puede reintentar con un PIN bueno) |
| IN-I | Tope diario | 20 registros con el mismo enlace en un día; el 21 | `INVITE_LIMIT`; al día siguiente se admite |
| IN-J | Registro con Google | token válido de Google, celular, consentimiento | vecino nuevo en la zona de Ana, sin PIN, `google_vinculado` verdadero, correo verificado, nombre tomado de Google, sesión abierta |
| IN-K | Avisos | un registro completado | Ana (quien invita) y el admin de zona, si es otro, tienen un aviso "se unió con tu enlace" dentro de la app, y no salió correo por ello |
| IN-L | Premio por referido | el nuevo hace su primer pedido y se liquida | Ana y el nuevo reciben S/ 3.00 de saldo (la regla ya existente, aplicada a un registro por enlace) |
| IN-M | Pendientes | 200 registros a medio hacer; el 201 | `SIGNUPS_FULL`; los vencidos no cuentan |
| IN-N | Sin sesión de otro | el registro con enlace no abre la sesión de nadie más ni cambia datos de Ana | — |

## Fuera de esta iteración (anotado)

- **Código QR imprimible** para pegar en la portería: se hace después de validar el enlace.
- **Verificar el celular por SMS**: tiene costo, queda como supuesto S-241.
- Que el admin de zona apruebe a cada vecino nuevo (opción B de la conversación del 20/10).

# Iteración 51 · Cierre de huecos para pasar a `main`

## Requisito

Como equipo, queremos que lo que quedó "fuera" de la iteración 50 se cierre antes de pasar la rama a `main`: límites por dirección para que nadie pruebe PIN ni mande correos sin freno, menos datos públicos de las zonas, códigos que nunca terminan en los registros del servidor, cabeceras de seguridad en todas las respuestas y una web que no se rompe ante una respuesta rara y carga menos al entrar.

## Por qué

- El bloqueo es por cuenta (S-68): desde una sola dirección se puede probar un PIN común contra todas las cuentas (100, 101, 102...) sin que nada lo frene.
- `/api/pin/olvide`, el registro por invitación y su código mandan correos sin límite por dirección; con un solo enlace se pueden mandar códigos a 200 direcciones cada 10 minutos desde el Gmail de Yapa.
- `GET /api/zonas` es pública y entrega el contacto de recepción (texto libre, puede ser un celular), el número de cliente del admin y la ubicación exacta (Ley 29733).
- En modo servidor sin SMTP, `ConsoleMailer` escribe los códigos de recuperación en la consola, que termina en los registros del servidor.
- Las respuestas de la API y de la web HTML no llevan cabeceras de seguridad; ninguna lleva CSP ni HSTS.
- Las sesiones vencidas solo se borran si alguien vuelve a usarlas.
- La web lee toda respuesta como JSON: un 502 del proxy en HTML rompe la pantalla con un error de JavaScript.
- La web baja 639 KB de JavaScript al entrar (el panel del equipo y el mapa van incluidos aunque el vecino no los use).

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-263 | **Dirección del cliente**: la del socket; si la petición viene de esta misma máquina (el proxy, p. ej. Caddy) y trae `X-Forwarded-For`, la **última** dirección de esa cabecera (la que agregó el proxy). Nunca se confía en la cabecera si la conexión viene de afuera. | proxy local |
| S-264 | **Límite de entradas fallidas por dirección**: 30 en 15 minutos (entrar con PIN o clave, restablecer el PIN con código, confirmar el registro). Al pasarlo, 15 minutos sin poder intentar desde esa dirección. Es alto a propósito: en el Perú muchos celulares salen a internet con la misma dirección. | 30 / 15 min |
| S-265 | **Límite de correos por dirección**: 10 por hora (olvidé mi PIN, código del registro por invitación). En "olvidé mi PIN" la respuesta no cambia (S-196): simplemente no sale el correo. | 10 / hora |
| S-266 | **Límite de códigos por enlace de invitación**: 10 por hora, sumando todos los correos que se registren con ese enlace. | 10 / hora |
| S-267 | **Zonas para quien no entró**: nombre, distrito, estado, vecinos y la ubicación redondeada a 3 decimales (unos 100 m). Sin contacto de recepción ni admin. Quien entró como vecino tampoco ve el contacto ni el admin de otras zonas; el equipo ve todo. | sin contacto |
| S-268 | **Correo en modo servidor**: sin `YAPA_SMTP_USER` y `YAPA_SMTP_PASSWORD`, el motor avisa al arrancar y **no** manda ni escribe los correos; la acción que necesita correo responde que no se pudo enviar. | nunca a la consola |
| S-269 | **Cabeceras** en toda respuesta: `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy` y una CSP que permite solo lo propio, Google (entrar con Google) y los mapas de OpenStreetMap. Con `YAPA_PUBLIC_URL` en https, también HSTS de un año. | CSP + HSTS |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| SG-08 | `client_ip(environ)` sigue S-263. | — |
| SG-09 | Con 30 fallos de entrada desde una dirección en 15 minutos, `POST /api/sesion`, `/api/pin/restablecer`, `/api/invitaciones/{c}/confirmar` y `/entrar` (web HTML) responden 429 sin revisar la clave. Una entrada buena no borra los fallos. | `TOO_MANY_ATTEMPTS` |
| SG-10 | Con 10 correos desde una dirección en una hora, `/api/invitaciones/{c}/correo` responde 429 y `/api/pin/olvide` responde igual que siempre sin mandar el correo. | `TOO_MANY_ATTEMPTS` |
| SG-11 | Un enlace de invitación que ya mandó 10 códigos en la última hora no manda más. | `INVITE_CODE_LIMIT` |
| SG-12 | `GET /api/zonas` sigue S-267. | — |
| SG-13 | `mailer_from_env(env, server=True)` sin credenciales devuelve un cartero que siempre falla con `MailError` y no escribe el mensaje. | — |
| SG-14 | `produccion.compose` agrega las cabeceras de S-269 a toda respuesta (API, web HTML, archivos y `/salud`); HSTS solo con `secure=True`. | — |
| SG-15 | Al abrir una sesión se borran las vencidas. | — |
| SG-16 | `POST /api/sesion/volver` no vuelve a una sesión del admin cuya credencial cambió. | `NOT_VIEWING_AS` |
| FE-SG-1 | Una respuesta que no es JSON se muestra como un error normal de Yapa, no como un error de JavaScript. | `BAD_RESPONSE` |
| FE-SG-2 | El panel del equipo y el mapa se cargan cuando se abren: el archivo principal pesa menos de 500 KB. | — |
| UX-01 | El ingreso dice "Con tu correo, celular o número de cliente y tu PIN de 6 dígitos." | — |
| UX-02 | El vecino ve "semana del 28 sep" en vez de `2026-W40` (portada, mis pedidos, mi zona y el recordatorio por WhatsApp). El panel del equipo sigue con el código. | — |
| UX-03 | La insignia "N % menos que en X" dice al pasar el cursor (y al lector de pantalla) la fecha en que se vio ese precio. | — |

## Criterios de aceptación

Motor (`tests/test_cierre_huecos.py`):

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| SG-O | Dirección | socket `203.0.113.5`; socket `127.0.0.1` con `X-Forwarded-For: 1.1.1.1, 198.51.100.7`; socket de afuera con la cabecera | `203.0.113.5`; `198.51.100.7`; la del socket |
| SG-P | Entradas fallidas | 30 PIN malos desde una dirección a cuentas distintas | el 31.º, aun con el PIN bueno, da 429 `TOO_MANY_ATTEMPTS`; otra dirección entra; 15 min después entra |
| SG-Q | Web HTML | 30 fallos en `/entrar` | el siguiente da 429 |
| SG-R | Correos por dirección | 11 "olvidé mi PIN" desde una dirección, a cuentas con correo | salen 10 correos; la 11.ª responde 200 igual |
| SG-S | Correos por enlace | 11 registros con el mismo enlace y correos distintos, desde direcciones distintas | el 11.º da `INVITE_CODE_LIMIT` |
| SG-T | Zonas | `GET /api/zonas` sin sesión, como vecino y como admin | sin `contacto` ni `admin` y con 3 decimales; sin `contacto` ni `admin`; completo |
| SG-U | Correo en servidor | `mailer_from_env({}, server=True).send(...)` | `MailError`, nada en la consola; con credenciales, `SmtpMailer` |
| SG-V | Cabeceras | `/api/estado`, `/`, `/salud` por `compose` con `secure=True` | las tres llevan CSP, `nosniff` y HSTS; con `secure=False`, sin HSTS |
| SG-W | Sesiones vencidas | sesión de hace 9 h, otra persona entra | la vieja ya no está en memoria |
| SG-X | Volver con credencial cambiada | ver como, se cambia la clave del admin global, volver | `NOT_VIEWING_AS` |

Web (`vitest`): FE-SG-1 en `api.test.ts`; UX-01 en `authDialog.test.ts`; UX-02 en `week.test.ts`. FE-SG-2 se comprueba con `npm run build` sin aviso de tamaño.

## Trazabilidad

| Regla / supuesto | Código | Prueba |
|---|---|---|
| SG-08, S-263 | `produccion.client_ip` | SG-O, y SG-P detrás del proxy |
| SG-09, S-264 | `throttle.Throttle`; `counting_failures` en `api.py` (entrar, restablecer, confirmar el registro); `entrar` en `app.py` | SG-P (3), SG-Q |
| SG-10, S-265 | `mails` en `pin_olvide` e `invitacion_correo` | SG-R |
| SG-11, S-266 | `invitations.CODES_PER_HOUR` en `start_signup` | SG-S |
| SG-12, S-267 | `zonas` en `api.py` | SG-T |
| SG-13, S-268 | `mailer.DisabledMailer`, `mailer_from_env(server=...)`; `web/__main__.py` lo pide con `--base` | SG-U |
| SG-14, S-269 | `produccion.CSP`, `SECURITY`, `HSTS`; `compose(secure=...)` las agrega a toda respuesta | SG-V (2) |
| SG-15 | `open_session` borra las vencidas; `app.sessions` para la prueba | SG-W |
| SG-16 | `sesion_volver` compara el `stamp` de la sesión del admin | SG-X |
| FE-SG-1 | `services/api.ts` | `api.test.ts` |
| FE-SG-2 | `LazyZonesMap.tsx` y `lazy(AdminPanel)` en `App.tsx`: el archivo principal pasa de 639 KB a 447 KB | `npm run build` sin aviso |
| UX-01 | `AuthDialog.LOGIN_HINT` | `authDialog.test.ts` |
| UX-02 | `utils/week.weekLabel` en la portada, `OrdersPage` y `ZonePage` | `week.test.ts` (3) |
| UX-03 | `Catalog`: `title` y texto para lector de pantalla con `shortDate` | `week.test.ts` |
| Pulido | `.nav-link` con `gap` (el ícono de Mi zona ya no queda pegado), `.nowrap` en "baja a S/ …" | revisado en el navegador |

Cambios en pruebas existentes (escenario, no aserciones): `test_in_i_tope_diario` espacia los 21 registros cada 6 minutos y `test_in_m_pendientes` usa 20 enlaces desde 20 conexiones, porque S-265 y S-266 ya no dejan mandar 20 o 200 códigos en minutos desde un solo enlace y una sola dirección. Los topes que prueban (S-239) siguen iguales.

Prueba real: la web construida servida por el motor (`--estaticos ../dist`) con la CSP: portada, Mi zona con el mapa de OpenStreetMap y el centro de operaciones cargan sin errores en la consola. Las dependencias de desarrollo se actualizaron con `npm audit fix` (0 vulnerabilidades).

Para producción: Caddy (o el proxy que se use) debe correr en la misma máquina para que S-263 lea la dirección real; si no hay SMTP configurado, los correos no salen (S-268) y el motor lo avisa al arrancar.

Evidencia: `docs/evidencia/desarrollo/51-cierre-huecos-rojo.txt`, `51-cierre-huecos-verde.txt`, `51-web-rojo.txt` y `51-web-verde.txt`.

## Fuera de esta iteración (anotado)

- El bloqueo por cuenta (S-68) todavía sirve para dejar fuera a un vecino a propósito (5 fallos). Cambiarlo es una decisión del equipo: por ejemplo, bloquear la cuenta solo para la dirección que falló.
- Las sesiones viven en memoria: un reinicio saca a todos.
- `persistence.save` reescribe la base completa en cada cambio; sirve para el piloto.

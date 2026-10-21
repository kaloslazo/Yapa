# Iteración 50 · Endurecimiento antes de abrir

> El número 49 queda reservado para el registro abierto con ubicación (anotado en la iteración 48).

## Requisito

Como equipo, queremos cerrar los huecos de seguridad que encontró la revisión de la rama `carlos/motor-y-roles` (21/10/2026) antes de abrir `holayapa.app` a vecinos reales: que nadie pueda llenar el disco ni congelar el servidor, que cambiar el PIN saque a quien tenía la sesión, y que "ver como" no pueda sacar dinero a nombre de otro.

## Por qué

- Cualquier petición, **incluso sin sesión**, podía traer un archivo `foto_archivo` y el motor lo guardaba en disco aunque la ruta no usara fotos (p. ej. `POST /api/pin/olvide`). El contenido no se revisaba: un `.png` podía ser HTML.
- El cuerpo de la petición se leía entero en memoria, sin tope, **dentro del cerrojo** que atiende una petición a la vez (S-232): una subida grande o lenta congelaba a todos.
- Cambiar o recuperar el PIN no cerraba las sesiones abiertas: quien robó una sesión seguía dentro hasta 8 horas.
- En "ver como" (S-257) el admin global podía pedir la devolución del saldo, cancelar pedidos con devolución y transferir una zona a nombre del vecino.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-259 | **Tope del cuerpo**: el servidor rechaza una petición de más de **9 MB** (la foto de 8 MB, S-151, más el formulario) sin leerla, y lee el cuerpo **antes** de tomar el cerrojo. | 9 MB, 413 |
| S-260 | **Fotos**: solo se guardan en las rutas que las usan (reclamo del vecino, bolsa, entrega y entrega fallida del admin), después de comprobar sesión y CSRF, y solo si el contenido **es** una imagen JPEG, PNG, WebP o HEIC (se mira el inicio del archivo, no el nombre). La extensión guardada sale del contenido. | 4 rutas, 4 tipos |
| S-261 | **Sesiones y PIN**: una credencial nueva (cambiar el PIN, recuperarlo con código, el PIN nuevo que da el admin, crear el PIN) cierra **todas** las sesiones de esa persona; quien hizo el cambio estando dentro sigue dentro. | cierra las demás |
| S-262 | **"Ver como" sin sacar dinero**: además de las credenciales (DM-08), desde "ver como" no se puede pedir la devolución del saldo, cancelar un pedido ni transferir una zona. Pedir, pagar y reclamar siguen permitidos para revisar el proceso (S-257). | 3 acciones más |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| SG-01 | `produccion.locked` lee el cuerpo antes de tomar el cerrojo; si `CONTENT_LENGTH` pasa de `MAX_BODY` (9 MB) responde 413 sin leerlo ni llamar a la aplicación. Bajo `/api/` la respuesta es JSON. | `PAYLOAD_TOO_LARGE` |
| SG-02 | Un archivo `foto_archivo` en una ruta que no usa fotos se ignora: no se escribe nada en disco. | — |
| SG-03 | En la web HTML (`app.py`) la foto se guarda recién después de comprobar sesión, rol y CSRF. | — |
| SG-04 | Una foto cuyo contenido no empieza como JPEG, PNG, WebP o HEIC se rechaza y no se guarda. | `PHOTO_INVALID` |
| SG-05 | Toda sesión recuerda la credencial con la que se abrió; si la credencial de esa persona cambia, la sesión deja de valer (401 en la API, a `/entrar` en la web). | `LOGIN_REQUIRED` |
| SG-06 | Quien cambia o crea su PIN estando dentro conserva **su** sesión. | — |
| SG-07 | En "ver como", `POST /api/saldo/devolucion`, `/api/pedidos/{n}/cancelar` y `/api/zonas/{z}/transferir` se rechazan y nada cambia. | `DEBUG_SESSION_READONLY` |

## Criterios de aceptación (`tests/test_endurecimiento.py`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| SG-A | Cuerpo enorme | `CONTENT_LENGTH` de 9 MB + 1 en `/api/sesion` | 413 `PAYLOAD_TOO_LARGE`, la aplicación no se llama y no se lee nada |
| SG-B | Cuerpo normal | login de 101 a través de `locked` | 200 |
| SG-C | Foto anónima | multipart sin sesión a `/api/pin/olvide` con `foto_archivo` | 200, carpeta de fotos vacía |
| SG-D | Foto en ruta sin fotos | vecino con sesión, multipart a `/api/avisos/leer` | carpeta vacía |
| SG-E | Foto que no es imagen | admin, `/api/admin/bolsas` con `<html>` llamado `x.png` | 422 `PHOTO_INVALID`, carpeta vacía |
| SG-F | Foto PNG llamada `.jpg` | admin, bolsa con un PNG real llamado `bolsa.jpg` | se guarda como `.png` |
| SG-G | Web HTML sin sesión | `POST /reclamos` multipart sin sesión | redirige a `/entrar`, carpeta vacía |
| SG-H | Recuperar el PIN cierra sesiones | 101 dentro en dos navegadores; recupera con código | las dos sesiones dan 401; el PIN nuevo entra |
| SG-I | Cambiar el PIN | 101 dentro en A y B; cambia el PIN en A | A sigue dentro, B da 401 |
| SG-J | PIN nuevo del admin | 101 dentro; el admin le da un PIN nuevo | 101 da 401 |
| SG-K | Crear el PIN (Google) | vecino sin PIN dentro; crea su PIN | sigue dentro |
| SG-L | Web HTML | 101 dentro en la web; cambia el PIN en la API | la web lo manda a `/entrar` |
| SG-M | "Ver como" sin sacar dinero | `debug-global` ve como 101 y pide devolución, cancela, transfiere zona | `DEBUG_SESSION_READONLY` y saldo, pedidos y zona sin cambios |
| SG-N | "Ver como" sigue sirviendo | ve como 105 y cotiza | 200 |

## Fuera de esta iteración (anotado)

- Límite de intentos por IP y bloqueo que no sirva para dejar fuera a un vecino a propósito (hoy el bloqueo es por cuenta, S-68).
- `/api/zonas` pública muestra coordenadas exactas, el contacto de recepción y el número del admin de zona (Ley 29733): decidir qué ve quien no entró.
- Tope por enlace de invitación a los correos con código (hoy una persona con un enlace puede mandar códigos a muchas direcciones).
- En modo servidor sin SMTP, los códigos salen en la consola del motor.
- Cabeceras CSP y HSTS; purgar sesiones vencidas.

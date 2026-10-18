# Iteración 33 · El admin ve la foto del reclamo y confirma lo que mueve dinero o zonas

## Requisito

Como admin de Yapa, quiero ver la foto del reclamo antes de aprobarlo o rechazarlo, y que verificar un pago o resolver un reclamo me pida confirmar.

Como admin de zona, quiero que "Pedir unión" y "Separar mi zona" me pidan confirmar, porque cambian cómo cuenta mi grupo para el mínimo.

## Por qué

Auditoría de diseño del 18/10/2026:

- La columna "Foto" de reclamos muestra solo el nombre del archivo. El admin decide dinero sin ver la prueba. La API guarda la foto (S-151) pero no la entrega.
- Verificar un pago, aprobar o rechazar un reclamo, pedir unión y separar la zona se ejecutan con un toque.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-179 | Solo el admin de Yapa puede ver las fotos guardadas (reclamos, bolsas, entregas). El vecino no ve fotos de otros. | solo admin |
| S-180 | La foto se pide por su ruta (`fotos/<nombre>`); solo se entregan archivos de imagen que están dentro de la carpeta de fotos. Cualquier otra ruta se rechaza. | — |
| S-181 | Al aprobar o rechazar un reclamo, verificar un pago, pedir unión o separar la zona, se pide una confirmación corta en la misma pantalla. Devolver lo mismo a otra pantalla no cambia el resultado. | — |

## Reglas

| Regla | Comportamiento |
|---|---|
| FA-01 | `GET /api/admin/foto?ruta=fotos/<nombre>` devuelve la imagen con su tipo (`image/jpeg`, `image/png`, `image/webp`, `image/heic`), `Cache-Control: private, no-store` y `X-Content-Type-Options: nosniff`. |
| FA-02 | Sin sesión responde 401 `LOGIN_REQUIRED`; con sesión de vecino, 403 `FORBIDDEN`. |
| FA-03 | Una ruta que no tiene la forma `fotos/<16 caracteres hex>.<tipo permitido>` (por ejemplo con `..`, con barras extra, con letras raras o vacía) responde 422 `INVALID_INPUT`. No se toca el disco. |
| FA-04 | Una ruta válida cuyo archivo no existe responde 404 `PHOTO_NOT_FOUND`. |
| FA-05 | Reclamos del admin: cada fila muestra la miniatura de la foto; al tocarla se abre grande. Si falla la carga, se muestra "No se pudo cargar la foto" y se puede decidir igual. |
| FA-06 | Aprobar y Rechazar un reclamo piden confirmar con el vecino, el artículo y el efecto ("se devuelve S/ X como saldo" / "no se devuelve nada"). |
| FA-07 | Verificar un pago pide confirmar con el código y el monto. |
| FA-08 | "Pedir unión" y "Separar mi zona" piden confirmar y dicen el efecto sobre el mínimo del grupo. |

## Criterios de aceptación (`api/tests/test_api_fotos.py` y pruebas del frontend)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| FA-A | El admin ve una foto guardada | admin, ruta de una foto en la carpeta | 200, `image/jpeg`, mismos bytes, `nosniff` |
| FA-B | Sin sesión | sin cookie | 401 `LOGIN_REQUIRED` |
| FA-C | Vecino | sesión de vecino | 403 `FORBIDDEN` |
| FA-D | Ruta con `..` | `fotos/../secreto.txt` | 422 `INVALID_INPUT` |
| FA-E | Ruta con tipo no permitido | `fotos/0123456789abcdef.txt` | 422 `INVALID_INPUT` |
| FA-F | Ruta vacía o sin parámetro | — | 422 `INVALID_INPUT` |
| FA-G | Foto que no existe | `fotos/0123456789abcdef.jpg` | 404 `PHOTO_NOT_FOUND` |
| FA-H | Ruta absoluta | `/etc/passwd` y `C:/Windows/win.ini` | 422 `INVALID_INPUT` |
| FA-I | Una foto subida por un reclamo se puede ver | vecino reclama con foto, admin pide la ruta que devolvió la API | 200 con los mismos bytes |
| FA-J | `photoUrl(ruta)` arma la dirección | `fotos/aa.jpg` | `/api/admin/foto?ruta=fotos%2Faa.jpg` |
| FA-K | `claimEffect(...)` dice el efecto | aprobar con S/ 5.38 / rechazar | "se devuelve S/ 5.38 como saldo" / "no se devuelve nada" |

Las reglas FA-05 a FA-08 de pantalla se verifican en el navegador y quedan en el registro.

## Fuera de esta iteración

Ventana de entrega del sábado y avisos por WhatsApp (regla de negocio del equipo), contadores y búsqueda del admin de Yapa, lista de invitados del admin de zona.

## Trazabilidad (regla → código → prueba)

| Regla | Código | Prueba |
|---|---|---|
| FA-01..FA-04 | `admin_foto` y `PHOTO_PATH` en `src/yapa_sdd/web/api.py`; el cuerpo en bytes se entrega con sus cabeceras | `tests/test_api_fotos.py` (FA-A, B, C, D, G, I) |
| FA-03 | `PHOTO_PATH.fullmatch`: solo `fotos/<16 hex>.<jpg, jpeg, png, webp, heic>` | `test_fa_d_rutas_invalidas` (9 rutas: `..`, `.txt`, vacía, absoluta, Windows, barra extra, NUL, otra carpeta, mayúsculas) |
| FA-05 | `ClaimPhoto` en `src/components/AdminPanel.tsx`, `photoUrl` en `src/utils/admin.ts` | FA-J (`src/utils/admin.test.ts`); la miniatura con un reclamo real no se pudo ver en la demo (ver abajo) |
| FA-06 | `ConfirmAction` en reclamos, `claimEffect` | FA-K |
| FA-07 | `ConfirmAction` en "Verificar" | navegador: "¿Ya viste S/ 72.76 con el código DEMO-40-109 en tu Yape?" |
| FA-08 | `ConfirmAction` en `ZonePage.tsx` | revisión de código; mismo componente |

Lo que no se pudo ver: la semana de demo ya cerró el plazo de 24 horas para reclamar (`CLAIM_WINDOW_CLOSED`), así que no hay un reclamo real con foto para mirar la miniatura. Se comprobó la foto por la API a través del proxy (200, `image/png`, `nosniff`, `no-store`) y la ruta completa subida → guardada → vista en la prueba FA-I.

Detalle encontrado: si un reclamo falla por una regla, la foto igual se guarda antes (hábito de la iteración 26, S-151). Queda como pregunta para el equipo (limpiar fotos huérfanas). Se agregó `fotos/` al `.gitignore` para que las fotos de vecinos no lleguen al repositorio.

Evidencia: `33-fotos-rojo.txt`, `33-fotos-front-rojo.txt`, `33-fotos-verde.txt` (346 pruebas del motor) y `33-fotos-front-verde.txt` (32 del frontend). Tipos y build sin errores.

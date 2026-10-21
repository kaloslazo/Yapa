# Iteración 39 · Fotos sin dueño y "Olvidé mi PIN"

## Requisito

1. Como equipo de Yapa, quiero que una foto subida en una acción que falla no se quede guardada, porque son fotos de vecinos sin ningún pedido que las explique.
2. Como vecino, quiero poder pedir ayuda si olvidé mi PIN sin tener que conocer a nadie del equipo, y como admin de Yapa, quiero ver esas solicitudes en un solo lugar y atenderlas con lo que ya existe (PIN nuevo y mensaje por WhatsApp).

## Por qué

- Auditoría de la iteración 33: `dispatch` guarda la foto *antes* de validar la acción. Un reclamo fuera de plazo (`CLAIM_WINDOW_CLOSED`) deja un archivo en `fotos/` que nadie referencia. Es un dato personal guardado sin motivo (Ley 29733).
- El PIN olvidado hoy solo se resuelve si el vecino ya sabe a quién escribir. El motor ya sabe generar un PIN nuevo y quitar el bloqueo (iteración 24); falta el pedido y la cola.
- **No hace falta un bot para el piloto.** No guardamos correo (solo número de cliente y celular), y el PIN nuevo ya se manda por WhatsApp con un enlace que el admin abre (`wa.me`). Un bot (API de WhatsApp Business) o correo se justifican cuando el volumen supere lo que un admin atiende a mano, y piden decisiones del equipo (número de empresa, plantillas, costo, guardar correos).

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-194 | **Sin bot ni correo en el piloto.** El sistema no envía mensajes. El admin escribe por WhatsApp al celular que el vecino registró y le pasa el PIN nuevo: quien no tiene ese celular no recibe el PIN. | — |
| S-195 | No se guarda correo ni se pide ningún dato nuevo para recuperar el PIN: solo el número de cliente. | — |
| S-196 | **Respuesta única.** Pedir ayuda con el PIN contesta siempre lo mismo, exista o no el número, para no revelar quién está registrado. | — |
| S-197 | **Una solicitud abierta por vecino.** Repetir el pedido no crea otra. Tope de 100 solicitudes abiertas en total: pasado el tope se sigue respondiendo lo mismo, pero no se guarda (evita inundar el panel). | 1 por vecino, 100 en total |
| S-198 | El admin atiende una solicitud con **Nuevo PIN** (que también la cierra) o la **descarta** si sospecha que no es el vecino. | — |
| S-199 | Las solicitudes viven en memoria, como las de unión de zonas: si el motor se reinicia se pierden y el vecino vuelve a pedir. | — |
| S-200 | El PIN nuevo nunca se muestra a quien lo pide: solo lo ve el admin, que lo manda al celular registrado. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| PH-01 | Si la acción que recibió una foto falla (cualquier error), el archivo guardado en esa petición se borra. | el de la acción |
| PH-02 | Si la acción funciona, la foto queda guardada y se sigue viendo como antes. | — |
| PH-03 | Solo se borra el archivo guardado en esa misma petición, nunca otra ruta. | — |
| OP-01 | `POST /api/pin/olvide` con `usuario` (número de cliente), sin sesión, responde siempre `{"mensaje": ...}` con el mismo texto, exista o no el vecino. | — |
| OP-02 | Si el número es de un vecino registrado, se crea una solicitud abierta con su número y la hora. | — |
| OP-03 | Si ya hay una solicitud abierta de ese vecino, no se crea otra (S-197). | — |
| OP-04 | Con 100 solicitudes abiertas no se guardan más y la respuesta no cambia (S-197). | — |
| OP-05 | Un `usuario` vacío o que no es un número entero da `INVALID_INPUT` (solo se revisa el formato, no si existe). | `INVALID_INPUT` |
| OP-06 | `GET /api/admin/pin-solicitudes` (solo admin) lista las abiertas, de la más antigua a la más nueva: id, número de cliente, nombre, celular y hora. | `FORBIDDEN`, `LOGIN_REQUIRED` |
| OP-07 | Generar un PIN nuevo a un vecino (`POST /api/admin/vecinos/<id>/pin`, ya existente) cierra sus solicitudes abiertas. | — |
| OP-08 | `POST /api/admin/pin-solicitudes/<id>/descartar` cierra una solicitud sin cambiar el PIN. Una que no existe da `PIN_REQUEST_NOT_FOUND`. | `PIN_REQUEST_NOT_FOUND` |
| OP-09 | La respuesta de OP-01 y la lista de OP-06 nunca contienen un PIN. | — |
| OP-10 | En pantalla: el ingreso del vecino tiene "¿Olvidaste tu PIN?", que pide el número de cliente y muestra el mensaje fijo. | — |
| OP-11 | En pantalla: la sección Vecinos del admin muestra "Solicitudes de PIN" arriba, cada una con "Nuevo PIN y escribir" (abre WhatsApp al celular registrado) y "Descartar"; el menú muestra cuántas hay. | — |

## Criterios de aceptación

Motor (`tests/test_api_fotos.py` y `tests/test_pin_olvidado.py`):

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| PH-A | Acción que falla borra la foto | el admin sube una foto de bolsa para un pedido que no existe | 422 y la carpeta de fotos queda vacía |
| PH-B | Acción que funciona la conserva | bolsa válida con foto (prueba FA-I existente) | la foto sigue guardada y se ve |
| OP-A | Misma respuesta | número de un vecino y número que no existe | el mismo texto y el mismo estado 200 |
| OP-B | Se crea y se lista | vecino 101 pide ayuda | el admin ve una solicitud con su nombre y celular |
| OP-C | No se duplica | 101 pide dos veces | una sola solicitud |
| OP-D | Tope | 100 vecinos abiertos y un vecino 101 más | sigue 200 con el mismo texto y no se guarda la 101 |
| OP-E | Formato | `usuario` vacío y `abc` | 422 `INVALID_INPUT` |
| OP-F | Solo admin | vecino o sin sesión pide la lista | 403 `FORBIDDEN` o 401 `LOGIN_REQUIRED` |
| OP-G | PIN nuevo la cierra | admin genera PIN al 101 | la lista queda vacía y el 101 entra con el PIN nuevo |
| OP-H | Descartar | admin descarta | la lista queda vacía y el PIN anterior sigue valiendo |
| OP-I | Descartar inexistente | id 999 | 422 `PIN_REQUEST_NOT_FOUND` |
| OP-J | Sin PIN en ninguna respuesta | OP-01 y OP-06 | el texto de las respuestas no contiene el PIN del vecino |

Las reglas de pantalla (OP-10, OP-11) se verifican en el navegador.

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| PH-01..PH-03 | `try/except` alrededor del manejador en `dispatch`, `src/yapa_sdd/web/api.py` | PH-A (`test_api_fotos.py`); PH-B es FA-I existente |
| OP-01 | `pin_olvide` en `api.py`, `customers.request_pin_help` | OP-A, OP-J |
| OP-02..OP-04 | `request_pin_help` y `store.pin_requests` | OP-B, OP-C, OP-D |
| OP-05 | formato en `request_pin_help` | OP-E |
| OP-06, OP-09 | `admin_pin_solicitudes` | OP-B, OP-F, OP-J |
| OP-07 | cierre de solicitudes en `customers.reset_pin` | OP-G |
| OP-08 | `dismiss_pin_request`, `admin_pin_descartar` | OP-H, OP-I |
| OP-10 | "¿Olvidaste tu PIN?" en `AuthDialog.tsx` | navegador: botón desactivado sin número y mensaje fijo |
| OP-11 | tarjeta "Solicitudes de PIN" en `Neighbors` (`AdminPanel.tsx`) y número en el menú | navegador: la solicitud de Carmen (cliente 105) aparece con "Nuevo PIN y escribir" y "Descartar" |

Evidencia: `docs/evidencia/desarrollo/39-fotos-pin-rojo.txt` (11 fallas antes del código) y `39-fotos-pin-verde.txt` (383 pruebas del motor, 11 nuevas; 55 del frontend).

Límites que conoce el equipo:
- Alguien podría llenar las 100 plazas pidiendo ayuda con números ajenos y dejar sin plaza a un vecino real. Para el piloto se acepta; el admin puede descartar, y después se puede limitar por dirección de origen.
- En la demo los vecinos sin alta no tienen celular registrado ("Sin celular"); los dados de alta sí, porque el alta lo exige.
- Un bot de WhatsApp o el correo no hacen falta ahora (S-194, S-195); se retoman cuando el volumen supere lo que un admin atiende a mano.

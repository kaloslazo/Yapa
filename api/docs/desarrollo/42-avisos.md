# Iteración 42 · Avisos dentro de la app y por correo

## Requisito

Como vecino, quiero enterarme dentro de Yapa (y, si quiero, también en mi correo) de lo que pasa con mi pedido y mi dinero sin tener que entrar a revisar. Como admin de zona, quiero que me avisen cuando otra zona pide unirse a la mía. Como Yapa, quiero que el aviso llegue solo a la persona concerniente y que un correo caído nunca rompa la acción que lo causó.

## Por qué

Decisión del equipo (18/10/2026): las notificaciones van **dentro de la app** (gratis, siempre disponibles) y **por correo** para lo importante. El correo ya es obligatorio y verificable (iteración 40). Los recordatorios de grupo por WhatsApp del admin de zona y la API de WhatsApp Business quedan fuera: esta iteración no manda nada por WhatsApp.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-216 | **Los avisos nacen de ocho hechos** (tabla de abajo) y solo los ve la persona concerniente. El equipo de Yapa no recibe avisos: usa su centro de operaciones. | 8 hechos |
| S-217 | **Correo solo de lo importante** (dinero, entrega, reclamo, devolución y pedido de unión), a un correo **verificado**, y solo si el vecino no lo apagó. Por defecto está activado. Verificar el pago y la respuesta a una unión se quedan dentro de la app para no llenar la bandeja. | por defecto activado |
| S-218 | Se guardan los últimos 50 avisos por vecino; los leídos siguen visibles. | 50 |
| S-219 | El correo sale **en segundo plano** (no hace esperar la respuesta) y se **intenta una sola vez**: si falla, el aviso sigue dentro de la app. Sin credenciales de correo, el motor lo imprime en su consola (como en la iteración 40). | 1 intento |
| S-220 | Un correo de aviso nunca lleva códigos ni PIN: cuenta qué pasó, con los montos, e invita a entrar a Yapa. Lleva una línea para apagarlos desde la cuenta. | — |
| S-221 | Los avisos se generan desde la API (la web HTML antigua no los genera). Quedan fuera por ahora: recordatorios por tiempo (por ejemplo "cierra el miércoles") y avisos del navegador (push). | — |

## Los ocho hechos

| Hecho | Aviso a | Tipo | Título | Correo |
|---|---|---|---|---|
| El equipo verifica un pago | dueño del pedido | `PAGO_VERIFICADO` | Verificamos tu pago | no |
| Se liquida la semana | dueño de cada pedido de la liquidación (los que el vecino canceló ya se resolvieron al cancelar y no entran) | `LIQUIDADO` | Cerramos tu pedido de la semana W | sí |
| Se entrega una zona | dueño de cada pedido de esa entrega | `ENTREGADO` | Tu pedido llegó a tu zona | sí |
| Falla la entrega de una zona | dueño de cada pedido | `NO_ENTREGADO` | No pudimos entregar tu pedido | sí |
| Se revisa un reclamo | quien reclamó | `RECLAMO_APROBADO` o `RECLAMO_RECHAZADO` | Aprobamos / No pudimos aprobar tu reclamo | sí |
| Se paga una devolución | quien la pidió | `DEVOLUCION_PAGADA` | Te devolvimos S/ X | sí |
| Una zona pide unirse a otra | admin de la zona pedida | `UNION_SOLICITADA` | La zona A quiere unirse a la tuya | sí |
| La otra zona acepta o rechaza | admin de la zona que pidió | `UNION_ACEPTADA` o `UNION_RECHAZADA` | Tu pedido de unión fue aceptado / rechazado | no |

Texto del aviso de liquidación, según cómo terminó el pedido: `LIQUIDADO` ("Pagaste S/ P y tu pedido costó S/ C. Te devolvimos S/ D a tu saldo." o, si no hubo devolución, sin la última frase), `NO_ATENDIDO` ("Tu zona no llegó al mínimo de pedidos. Te devolvemos S/ D.") `NO_ENTREGADO` ("No pudimos entregarlo. Te devolvimos S/ D a tu saldo.") y, para el pedido cuyo pago nunca se verificó, "No pudimos verificar tu pago a tiempo, así que tu pedido de esta semana no entró en la compra." (más "Te devolvimos S/ D a tu saldo." si había usado saldo). Los montos van con dos decimales.

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AV-01 | `GET /api/avisos` (vecino con sesión): `avisos` (más nuevos primero, cada uno con `id`, `tipo`, `titulo`, `texto`, `hora`, `leido`), `sin_leer`, `correo_avisos` (si el vecino quiere el correo) y `correo_verificado`. | `LOGIN_REQUIRED`, `FORBIDDEN` |
| AV-02 | `POST /api/avisos/leer {id}` marca un aviso como leído; sin `id` marca todos. Solo se pueden marcar los propios. Marcar uno ya leído no cambia nada. | `NOTICE_NOT_FOUND` |
| AV-03 | `POST /api/avisos/preferencias {avisos_correo}` (verdadero o falso) activa o apaga el correo de avisos. | `LOGIN_REQUIRED`, `FORBIDDEN` |
| AV-04 | `GET /api/sesion` del vecino agrega `avisos_sin_leer` y `correo_avisos`. | — |
| AV-05 | Cada hecho de la tabla crea el aviso con su tipo, título y texto. El texto nombra la semana, el pedido y los montos, con palabras de negocio. | — |
| AV-06 | **Privacidad:** un aviso solo lo ve su dueño. Los demás vecinos de la zona no reciben el aviso ni lo ven en su lista. | — |
| AV-07 | Se conservan los 50 más nuevos de cada vecino; al pasar de 50, se descarta el más antiguo. | — |
| AV-08 | Correo (S-217, S-219): solo para los tipos con "sí", con correo verificado y preferencia activa. Un aviso se manda una sola vez, aunque ocurran otras acciones después. | — |
| AV-09 | El correo tiene como asunto el título del aviso, el texto del aviso y la línea para apagarlos; no lleva códigos, PIN ni enlaces de entrada (S-220). | — |
| AV-10 | Si el correo falla, la acción que lo causó termina bien, la respuesta no cambia y el aviso sigue dentro de la app. | — |
| AV-11 | Si crear el aviso fallara, la acción que lo causó termina bien igual (un aviso nunca rompe un pedido, una entrega o una liquidación). | — |
| AV-12 | Los avisos y su estado de correo se guardan en la base (persistencia). | — |
| AV-13 | En pantalla: una campana en la barra con el número de avisos sin leer, un panel con la lista, "Marcar todo como leído", el interruptor "Avisarme también por correo" (solo si el correo está verificado; si no, un texto que invita a verificarlo), y cada aviso lleva a "Mis pedidos" o a "Mi zona". Se refresca cada minuto y al volver a la pestaña. | — |

## Criterios de aceptación (`tests/test_avisos.py`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| AV-A | Pago verificado | el equipo verifica el pedido de 101 | 101 tiene un aviso `PAGO_VERIFICADO` sin leer; `sin_leer` es 1 y `GET /api/sesion` también lo dice |
| AV-B | Solo el dueño | el pedido de 801 se verifica | el aviso está en la lista de 801, no en la de 802 |
| AV-C | Entrega | se entrega la zona con 8 pedidos | los 8 dueños reciben `ENTREGADO` |
| AV-D | Liquidación | se liquida la semana | cada dueño recibe `LIQUIDADO` con los montos pagado, costo y devuelto del pedido; quien canceló su pedido no recibe nada; quien no tuvo su pago verificado recibe el aviso de que su pedido no entró |
| AV-E | Entrega fallida | se registra la falla de una zona | los dueños reciben `NO_ENTREGADO` |
| AV-F | Reclamo | se aprueba y se rechaza un reclamo | `RECLAMO_APROBADO` con el monto devuelto y `RECLAMO_RECHAZADO` |
| AV-G | Devolución | el equipo marca una devolución pagada | `DEVOLUCION_PAGADA` con el monto |
| AV-H | Unión | una zona pide unirse y la otra acepta o rechaza | el admin de la zona pedida recibe `UNION_SOLICITADA`; el que pidió recibe `UNION_ACEPTADA` o `UNION_RECHAZADA`; nadie más recibe nada |
| AV-I | Leer uno | marcar un aviso | solo ese pasa a leído; `sin_leer` baja en 1 |
| AV-J | Leer todos | marcar sin `id` | `sin_leer` es 0 |
| AV-K | Ajeno o inexistente | marcar el aviso de otro vecino o el 9999 | `NOTICE_NOT_FOUND`, y el aviso del otro sigue sin leer |
| AV-L | Tope | 55 avisos para 101 | quedan 50, los más nuevos |
| AV-M | Correo de entrega | 101 con correo verificado y la entrega de su zona | un correo a su dirección, con el título como asunto y el texto del aviso |
| AV-N | Sin correo verificado | 101 sin verificar | ningún correo, pero el aviso sí existe |
| AV-O | Apagado | 101 apaga el correo | ningún correo; al volver a activarlo, los avisos nuevos sí lo mandan |
| AV-P | Pago verificado no manda correo | solo `PAGO_VERIFICADO` | ningún correo |
| AV-Q | Una sola vez | otra acción después del aviso | no se manda el mismo correo dos veces |
| AV-R | Correo caído | el envío falla | la acción responde igual que sin falla y el aviso existe |
| AV-S | Sin secretos | el correo y la lista de avisos | no contienen PIN ni códigos de pago |
| AV-T | Roles | sin sesión; admin de Yapa | 401 `LOGIN_REQUIRED`; 403 `FORBIDDEN` en las tres rutas |
| AV-U | Persistencia | guardar y cargar la base | los avisos, su estado de lectura y de correo se conservan |
| AV-V | Falla al avisar | crear el aviso lanza un error | la acción que lo causó responde 200 igual (AV-11) |

Las reglas de pantalla (AV-13) se verifican en el navegador y con pruebas de las funciones puras del frontend.

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| AV-01 | `avisos`, `notices.for_customer` (`src/yapa_sdd/web/api.py`, `notices.py`) | AV-A, AV-B, AV-L |
| AV-02 | `avisos_leer`, `notices.mark_read` | AV-I, AV-J, AV-K |
| AV-03 | `avisos_preferencias`, `notices.set_email_preference`; `Customer.email_notices` | AV-O |
| AV-04 | `me()` agrega `avisos_sin_leer` y `correo_avisos` | AV-A, AV-J, AV-O |
| AV-05 | los ocho hechos en `notices.py` (`payment_verified`, `cycle_settled`, `delivered`, `delivery_failed`, `claim_reviewed`, `refund_paid`, `merge_requested`, `merge_answered`) llamados desde los manejadores de la API | AV-A, AV-C, AV-D, AV-E, AV-F, AV-G, AV-H |
| AV-06 | cada aviso lleva el `customer_id` de su dueño; `for_customer` y `mark_read` filtran por él | AV-B, AV-H, AV-K |
| AV-07, S-218 | recorte por vecino en `notices.add` | AV-L |
| AV-08, S-217, S-219 | `EMAIL_KINDS`, `notices.claim_emails` y `send_notice_emails` (segundo plano) | AV-M, AV-N, AV-O, AV-P, AV-Q |
| AV-09, S-220 | cuerpo del correo en `claim_emails` | AV-M, AV-S |
| AV-10 | `send_notice_emails` atrapa `MailError` | AV-R |
| AV-11 | `tell` atrapa cualquier error al avisar | AV-V |
| AV-12 | `Notice` es un dataclass del paquete; `InMemoryStore.notices` y `_next_notice_id` | AV-U |
| AV-13 | `NoticeBell.tsx`, `utils/notices.ts`, bloque "Iteración 42" de `styles.css`, cableado en `App.tsx` | `utils/notices.test.ts` y navegador (ver abajo) |
| S-216 | los ocho hechos; el admin de Yapa no recibe avisos | AV-T |
| S-221 | los avisos se llaman desde la API, no desde la web HTML | — |

Una duda que apareció al probar: la liquidación incluye los pedidos cuyo pago nunca se verificó (el motor los marca `CANCELADO` al liquidar, distinto de lo que el vecino canceló). Esos reciben el aviso "No pudimos verificar tu pago a tiempo" (AV-D); los que el vecino canceló ya se resolvieron al cancelar y no avisan.

Pruebas de las propias pruebas (mutaciones a mano, revertidas, 15 en total): sin marcar el correo como enviado (AV-Q, AV-R, AV-U), sin revisar el correo verificado (AV-N), sin revisar la preferencia (AV-O), leer sin filtrar por dueño (AV-J, AV-K), sin tope o recortando los más nuevos (AV-L), el pago verificado mandando correo (AV-P), el aviso de unión aceptada al admin equivocado (AV-H), la lista con avisos ajenos (AV-B), un aviso que rompe la acción (AV-V), un correo caído que rompe la acción (AV-R), un pedido sin pago verificado con el texto de "pagaste" (AV-D), un PIN dentro del correo (AV-S), el correo sin la línea para apagarlo (AV-M) y "leer todos" que deja la mitad sin leer (AV-I). Una mutación sobrevivió al principio: mi prueba de la liquidación suponía que el motor liquida los pedidos cancelados por el vecino y no es así; se corrigió la spec y se agregó AV-D de pago sin verificar.

Pantalla, con la demo (motor con ConsoleMailer): con una solicitud de unión pendiente, la campana de Ana (admin de zona) muestra "1"; el panel lista el aviso con "ahora" (la hora sale del reloj del motor, no del navegador); al hacer clic se marca leído y lleva a "Mi zona". Sin correo verificado el panel invita a verificarlo; después de verificar el correo con el código de la consola, el panel muestra "Avisarme también por correo", y una segunda solicitud de unión mandó el correo (visto en la consola del motor). Apagar el interruptor lo guarda en el motor. A 390 px el panel cabe entero (16 a 355 px, sin barra horizontal) y la campana mide 44 × 44.

**Una limitación del navegador de pruebas:** este Chrome automatizado no devolvió la cookie de sesión al motor (también con el motor de la iteración 41, así que no es un error de esta iteración), por lo que la verificación en pantalla se hizo con un proxy local que guarda la cookie. El proxy es solo de la prueba y no está en el repositorio. En un navegador normal la cookie funciona como siempre.

Evidencia: `docs/evidencia/desarrollo/42-avisos-rojo.txt` (el módulo no existía) y `42-avisos-verde.txt` (465 pruebas del motor, 34 nuevas; 67 del frontend, 12 nuevas).

## Cómo activar el correo

Es el mismo envío de la iteración 40: con `YAPA_SMTP_USER` y `YAPA_SMTP_PASSWORD` los avisos importantes salen por correo real; sin esas variables se imprimen en la consola del motor. No hay nada nuevo que configurar. Desde la iteración 43 el correo sale con diseño, y los pasos para usar Resend con un dominio propio están en `43-correo-html.md`.

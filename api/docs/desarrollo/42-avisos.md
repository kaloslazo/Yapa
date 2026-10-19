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
| Se liquida la semana | dueño de cada pedido (menos los cancelados por el vecino) | `LIQUIDADO` | Cerramos tu pedido de la semana W | sí |
| Se entrega una zona | dueño de cada pedido de esa entrega | `ENTREGADO` | Tu pedido llegó a tu zona | sí |
| Falla la entrega de una zona | dueño de cada pedido | `NO_ENTREGADO` | No pudimos entregar tu pedido | sí |
| Se revisa un reclamo | quien reclamó | `RECLAMO_APROBADO` o `RECLAMO_RECHAZADO` | Aprobamos / No pudimos aprobar tu reclamo | sí |
| Se paga una devolución | quien la pidió | `DEVOLUCION_PAGADA` | Te devolvimos S/ X | sí |
| Una zona pide unirse a otra | admin de la zona pedida | `UNION_SOLICITADA` | La zona A quiere unirse a la tuya | sí |
| La otra zona acepta o rechaza | admin de la zona que pidió | `UNION_ACEPTADA` o `UNION_RECHAZADA` | Tu pedido de unión fue aceptado / rechazado | no |

Texto del aviso de liquidación, según cómo terminó el pedido: `LIQUIDADO` ("Pagaste S/ P y tu pedido costó S/ C. Te devolvimos S/ D a tu saldo." o, si no hubo devolución, sin la última frase), `NO_ATENDIDO` ("Tu zona no llegó al mínimo de pedidos. Te devolvemos S/ D.") y `NO_ENTREGADO` ("No pudimos entregarlo. Te devolvimos S/ D a tu saldo."). Los montos van con dos decimales.

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
| AV-D | Liquidación | se liquida la semana | cada dueño recibe `LIQUIDADO` con los montos pagado, costo y devuelto del pedido |
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

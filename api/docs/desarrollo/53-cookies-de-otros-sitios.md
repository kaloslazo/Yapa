# Iteración 53 · La sesión no se pierde por cookies de otros servicios

## Requisito

Como vecino que entró a Yapa, quiero seguir dentro cuando recargo la página, aunque el navegador tenga cookies de otros servicios (por ejemplo, la de Google).

## Por qué

El 22/10 se vio en producción que, después de mostrarse el botón de Google, cualquier recarga sacaba al usuario: la web volvía a mostrar "Ingresar". Google guarda en el navegador la cookie `g_state`, cuyo valor es un JSON con comillas y llaves (`g_state={"i_l":0}`). El motor leía la cabecera `Cookie` con `SimpleCookie` de Python, que deja de leer al encontrar un valor así; si `g_state` llegaba antes que `yapa_api`, la cookie de la sesión no se leía y el motor respondía 401. Comprobado con `curl` contra holayapa.app: la misma sesión entra sola o con `g_state` después, y se rechaza con `g_state` antes.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-277 | **La cookie de la sesión se busca por su nombre** entre todas las de la cabecera, separadas por `;`, sin importar qué traigan las demás. Una cookie ajena mal formada se ignora; nunca invalida la sesión. | se ignora |

## Reglas

| Regla | Comportamiento |
|---|---|
| CK-01 | La API (`yapa_api`) y la web HTML (`yapa_sesion`) leen su cookie aunque antes o después vengan cookies con comillas, llaves, comas o espacios. |
| CK-02 | Si la cookie aparece repetida, vale la primera (la del camino más específico, como la manda el navegador). |
| CK-03 | Sin la cookie de Yapa, no hay sesión, como antes. |

## Criterios de aceptación

| # | Criterio | Resultado |
|---|---|---|
| CK-A | Sesión abierta y cabecera `g_state={"i_l":0,"i_ll":1}; yapa_api=<token>`: `GET /api/sesion` responde 200 | 200 |
| CK-B | Lo mismo con `g_state` después de la cookie de Yapa | 200 |
| CK-C | Solo `g_state`, sin cookie de Yapa | 401 |
| CK-D | Web HTML: con `g_state` antes de `yapa_sesion`, `/cuenta` muestra la cuenta (200) | 200 |

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| CK-01 | `web/app.py` `_cookie` (usada por `current_session` y por `session_of` de `web/api.py`) | `test_ck_a_google_antes_no_saca_la_sesion`, `test_ck_b_google_despues_no_saca_la_sesion`, `test_ck_d_web_html_con_google_antes` |
| CK-02 | `_cookie` devuelve la primera coincidencia | `test_ck_a_*` |
| CK-03 | `_cookie` devuelve `None` sin la cookie | `test_ck_c_sin_cookie_de_yapa_no_hay_sesion` |

Evidencia: `docs/evidencia/desarrollo/53-cookies-rojo.txt` (2 fallos: CK-A y CK-D) y `53-cookies-verde.txt`. Resultado: 588 pruebas del motor en verde.

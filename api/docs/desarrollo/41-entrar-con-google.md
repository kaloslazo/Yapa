# Iteración 41 · Entrar con Google

## Requisito

Como vecino, quiero poder entrar a Yapa con mi cuenta de Google, sin escribir PIN, además del PIN y de la recuperación por código. Como Yapa, quiero que esto sea opcional y que no pueda usarse para entrar a la cuenta de otra persona.

## Por qué

Decisión del equipo (18/10/2026): permitir los dos mecanismos, el código por correo (iteración 40) y "Entrar con Google". Google verifica la identidad del dueño del correo y el vecino se ahorra el PIN.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-210 | **Opcional y complementa al PIN.** Se activa con el Client ID público del proyecto de Google Cloud (variable `YAPA_GOOGLE_CLIENT_ID`). Sin él, el botón no se muestra y el motor responde que no está configurado. | — |
| S-211 | **Solo entran con Google quienes vincularon su cuenta antes**, estando dentro con su PIN. La vinculación guarda el identificador estable de Google (`sub`), no el correo, porque el correo puede cambiar. | — |
| S-212 | Al vincular, si el vecino no tiene un correo verificado, el correo de Google (que Google ya verificó) pasa a ser su correo verificado, salvo que otro vecino ya use ese correo. Si ya tenía uno verificado, se conserva. | — |
| S-213 | Una cuenta de Google se vincula a un solo vecino, y un vecino a una sola cuenta de Google. Vincular otra cuenta reemplaza la anterior. Se puede desvincular; el PIN sigue valiendo. | — |
| S-214 | **Verificación en el motor** con PyJWT y las claves públicas de Google: firma RS256, `aud` igual al Client ID, `iss` de Google, no vencido y `email_verified` verdadero. Es una dependencia **opcional** (`PyJWT`): el resto del motor sigue usando solo la biblioteca estándar. Las llaves se piden a Google y se guardan una hora. | RS256 |
| S-215 | El equipo de Yapa (admin) no entra con Google: solo vecinos y admins de zona (que son vecinos). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| GO-01 | `GET /api/estado` agrega `google_client_id` (el público, o `null` si no está configurado) para que la pantalla sepa si muestra el botón. | — |
| GO-02 | `POST /api/cuenta/google {credential}` (vecino con sesión) vincula su cuenta de Google (S-211..S-213). | `LOGIN_REQUIRED`, `FORBIDDEN`, `GOOGLE_NOT_CONFIGURED`, `INVALID_GOOGLE_TOKEN`, `GOOGLE_ALREADY_LINKED` |
| GO-03 | `POST /api/sesion/google {credential}` (sin sesión): si esa cuenta de Google está vinculada, abre la sesión igual que con el PIN; si no, avisa cómo vincularla. | `GOOGLE_NOT_CONFIGURED`, `INVALID_GOOGLE_TOKEN`, `GOOGLE_NOT_LINKED` |
| GO-04 | `POST /api/cuenta/google/desvincular` (vecino con sesión) quita la vinculación. | `LOGIN_REQUIRED`, `FORBIDDEN` |
| GO-05 | El token se acepta solo si: firma RS256 válida con una llave de Google, `aud` igual al Client ID, `iss` de Google, no vencido (30 s de margen) y `email_verified` verdadero. Cualquier otro caso (otra firma, otra audiencia, otro emisor, vencido, algoritmo distinto de RS256) da el mismo error. | `INVALID_GOOGLE_TOKEN` |
| GO-06 | `GET /api/sesion` agrega `google_vinculado`. | — |
| GO-07 | En pantalla: con Client ID, el ingreso del vecino muestra "Entrar con Google" y la cuenta muestra "Vincular mi cuenta de Google" o, si ya está vinculada, "Cuenta de Google vinculada" con "Desvincular". Sin Client ID no aparece nada ni se carga ningún script de Google. | — |

## Criterios de aceptación (`tests/test_google.py`)

Las pruebas firman tokens de verdad con una llave RSA propia y la inyectan como si fuera la de Google, así que se ejercita la verificación real (no un doble que siempre dice que sí).

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| GO-A | Vincular | token válido con la sesión del vecino 101 | queda vinculada y `google_vinculado` es verdadero |
| GO-B | Entrar | después de vincular, el mismo token sin sesión | 200, `usuario` 101, y la cookie de esa sesión funciona |
| GO-C | Sin vincular | un token válido de otra cuenta | 422 `GOOGLE_NOT_LINKED` |
| GO-D | Firma ajena | token firmado con otra llave | `INVALID_GOOGLE_TOKEN` |
| GO-E | Otra audiencia | `aud` distinto | `INVALID_GOOGLE_TOKEN` |
| GO-F | Otro emisor | `iss` distinto | `INVALID_GOOGLE_TOKEN` |
| GO-G | Vencido | `exp` hace una hora | `INVALID_GOOGLE_TOKEN` |
| GO-H | Correo sin verificar | `email_verified` falso | `INVALID_GOOGLE_TOKEN` |
| GO-I | Algoritmos | token sin firma (`none`) y token HS256 con la llave pública como secreto | `INVALID_GOOGLE_TOKEN` los dos |
| GO-J | Sin configurar | motor sin Client ID | `GOOGLE_NOT_CONFIGURED` en las dos rutas |
| GO-K | Adopta el correo | vecino sin correo vincula | su correo verificado es el de Google |
| GO-L | No pisa un correo verificado | vecino con correo verificado distinto vincula | conserva el suyo |
| GO-M | Correo ya usado | el correo de Google es de otro vecino | vincula, pero no adopta el correo |
| GO-N | Una cuenta, un vecino | la misma cuenta de Google en otro vecino | `GOOGLE_ALREADY_LINKED` |
| GO-S | Reemplazo | vincular una segunda cuenta de Google | la primera deja de entrar y la segunda entra |
| GO-O | Desvincular | después de desvincular | entrar con Google da `GOOGLE_NOT_LINKED` y el PIN sigue entrando |
| GO-P | Roles | sin sesión o admin al vincular | `LOGIN_REQUIRED` o `FORBIDDEN` |
| GO-Q | Estado | `GET /api/estado` con y sin Client ID | `google_client_id` con el valor o `null` |
| GO-R | No hay secretos en respuestas | respuesta de `sesion/google` | no contiene el token ni el `sub` |

Las reglas de pantalla (GO-07) se verifican en el navegador hasta donde se pueda sin un Client ID real (la ventana de Google necesita el del proyecto del equipo).

## Trazabilidad

Se completa al terminar la implementación.

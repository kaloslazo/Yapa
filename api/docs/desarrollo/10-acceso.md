# Iteración 10 · Acceso con PIN y sesión

## Requisito

Como vecino, quiero que nadie más pueda ver mi saldo, registrar pedidos a mi nombre ni cancelarlos.

Como Yapa, quiero que las páginas de administración (verificar pagos, liquidar) solo las use el administrador.

## Por qué ahora

En la iteración 9, el supuesto S-60 dejaba entrar con solo escribir un número de cliente. Eso significa que cualquiera podía ver el saldo de otro o cancelar su pedido, y el saldo es plata del cliente (C-05). Esta iteración **reemplaza S-60 y S-61**.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-64 | El vecino entra con su número de cliente y un **PIN de 6 dígitos**. Es simple de usar en el celular, igual que Yape. | 6 dígitos |
| S-65 | El PIN inicial lo asigna el administrador al dar de alta al vecino (por ejemplo, se lo envía por WhatsApp). El vecino puede cambiarlo después indicando el PIN actual. | — |
| S-66 | No se aceptan PIN triviales: seis dígitos iguales (`111111`) ni secuencias (`123456`, `654321`). | — |
| S-67 | El PIN **nunca se guarda en texto**: se guarda su hash con sal (PBKDF2-SHA256, 200 000 iteraciones). | — |
| S-68 | Después de 5 intentos fallidos seguidos, la cuenta se bloquea 15 minutos. | 5 intentos / 15 min |
| S-69 | La sesión dura 8 horas. Se guarda en el servidor y el navegador solo tiene un identificador aleatorio en una cookie `HttpOnly` y `SameSite=Lax`. | 8 h |
| S-70 | El administrador entra con usuario y contraseña de al menos 10 caracteres. | ≥ 10 |
| S-71 | Todo formulario que cambia datos lleva un **token anti-falsificación** (CSRF) ligado a la sesión. | — |

## Reglas

| Regla | Comportamiento | Error / respuesta |
|---|---|---|
| AC-01 | El administrador asigna o el vecino cambia un PIN: 6 dígitos, no trivial (S-66). Solo se guarda el hash (S-67). Para cambiarlo, el vecino indica su PIN actual. | `INVALID_PIN`, `INVALID_CREDENTIALS` |
| AC-02 | Entrar: número de cliente + PIN correctos crean una sesión (S-69). Si algo no coincide, el error es **el mismo** exista o no el cliente, para no revelar quién está registrado. | `INVALID_CREDENTIALS` |
| AC-03 | Con 5 fallos seguidos, la cuenta queda bloqueada 15 minutos, aunque después se ponga el PIN correcto. Un acceso correcto reinicia el contador. | `ACCOUNT_LOCKED` |
| AC-04 | `/cuenta`, `/cotizar`, `/pedidos` y `/cuenta/cancelar` requieren sesión de vecino. El cliente es **siempre el de la sesión**: el campo `cliente` del formulario se ignora. Sin sesión → redirección a `/entrar`. El catálogo (`/`) sigue siendo público. | 303 a `/entrar` |
| AC-05 | `/admin` y sus acciones requieren sesión de administrador (S-70). Una sesión de vecino recibe 403. | 303 / 403 |
| AC-06 | Un POST con sesión debe incluir el token CSRF de esa sesión. Si falta o no coincide → 403 y no se hace nada. | 403 |
| AC-07 | `POST /salir` cierra la sesión: la misma cookie ya no sirve. | 303 a `/` |

## Criterios de aceptación

- **AA-01 · PIN válido.** El admin asigna `482915` al cliente 101 → se guarda un hash distinto del PIN. → AC-01, S-67
- **AA-02 · PIN inválido.** `12345`, `1234567`, `abcdef`, `111111`, `123456` y `654321` → `INVALID_PIN`. → AC-01, S-66
- **AA-03 · Entrar.** El 101 con `482915` entra y ve su cuenta. Un PIN incorrecto o un cliente inexistente → el mismo mensaje `INVALID_CREDENTIALS`. → AC-02
- **AA-04 · Bloqueo.** 5 fallos seguidos → el 6.º intento, aunque sea con el PIN correcto, da `ACCOUNT_LOCKED`. 15 minutos después, con el PIN correcto, entra. → AC-03
- **AA-05 · Sin sesión.** `GET /cuenta` sin sesión → 303 a `/entrar`. `GET /` → 200. → AC-04
- **AA-06 · No se puede actuar por otro.** Con sesión del 101, un POST a `/pedidos` con `cliente=105` registra el pedido **a nombre del 101**. → AC-04
- **AA-07 · Admin protegido.** Una sesión de vecino en `/admin` → 403. El admin con su contraseña → 200. Una contraseña de admin corta → `INVALID_PASSWORD`. → AC-05, S-70
- **AA-08 · CSRF.** Un POST a `/pedidos` con sesión válida pero sin token → 403 y no se crea ningún pedido. → AC-06
- **AA-09 · Salir.** Después de `POST /salir`, la cookie anterior lleva a `/entrar`. → AC-07
- **AA-10 · Cambiar PIN.** Con el PIN actual correcto se cambia; con uno incorrecto → `INVALID_CREDENTIALS`. → AC-01, S-65

## Cambios en criterios anteriores (iteración 9)

Con el acceso, cambian tres criterios de `09-interfaz-web.md`. Las pruebas se actualizan **antes** que el código:

- **WA-07:** `/cuenta` muestra la cuenta del vecino de la sesión, ya no la de un `?cliente=` de la URL. El caso "cliente inexistente → 404" desaparece: ahora ese cliente simplemente no puede entrar (AA-03).
- **WA-11:** para ver la cuenta con el nombre malicioso hay que entrar como ese cliente. Se sigue verificando que el nombre sale escapado.
- **WA-12:** el caso "cliente=abc" ya no aplica, porque el cliente viene de la sesión. Se reemplaza por una cantidad no numérica, que da 422 con `INVALID_QUANTITY`.

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| AC-01, S-66, S-67 | `auth.py` `_check_pin`, `set_pin`, `change_pin`, `_hash` | `test_access.py` `test_aa01_*`, `test_aa02_*`, `test_aa10_*`, `test_aa11_*` |
| AC-02 | `auth.py` `authenticate` (mismo error y mismo costo si el usuario no existe) · `web/app.py` `entrar` | `test_aa03_*` |
| AC-03, S-68 | `auth.py` `authenticate` (contador y bloqueo) | `test_aa04_*` |
| AC-04 | `web/app.py` `dispatch` (rol requerido) y handlers que usan `session.principal` | `test_aa05_*`, `test_aa06_*` |
| AC-05, S-70 | `web/app.py` `dispatch` · `auth.py` `set_admin_password` | `test_aa07_*` |
| AC-06, S-71 | `web/app.py` `dispatch` (`hmac.compare_digest` del token) · `views.hidden` | `test_aa08_*` |
| AC-07 | `web/app.py` `salir` | `test_aa09_*` |

## Nota sobre la velocidad de las pruebas

PBKDF2 con 200 000 iteraciones hace que cada acceso tarde a propósito (así cuesta adivinar un PIN). Con eso, la suite tardaba 24 s. Las pruebas web bajan las iteraciones a 1 000 solo mientras corren (`fast_hashing`), y la prueba AA-11 fija que el código de producción use 200 000. No se debilita ninguna aserción.

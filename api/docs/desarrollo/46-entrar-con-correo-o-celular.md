# Iteración 46 · Entrar con correo o celular

## Requisito

Como vecino, quiero entrar a Yapa con mi **correo o mi celular** y mi PIN, sin tener que acordarme de un "número de cliente". Y si me registré con Google, quiero entrar con Google y no necesitar una contraseña; si algún día quiero una, quiero crearla yo mismo desde Mi cuenta.

## Por qué

Hoy la pantalla de ingreso pide el "número de cliente" (101, 107…), un dato que nadie se sabe, que solo se ve dentro de la cuenta. Con el registro por invitación (iteración 45) quien entra con Google ni siquiera tiene PIN, así que cuando se le cierra la sesión no puede volver a entrar a mano. El dueño lo vio en la prueba del 21/10: "para iniciar sesión manualmente te tienes que saber tu número de cliente, y además te pide contraseña si te vinculaste con Google".

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-244 | El vecino entra con **correo, celular o número de cliente** (lo que escriba) más su PIN. El correo vale sin importar mayúsculas. Cuenta el correo registrado aunque aún no esté verificado, porque el PIN sigue siendo el que protege. El equipo de Yapa (admin) sigue con su usuario y contraseña. | tres formas de entrar |
| S-245 | Si lo escrito no corresponde a nadie, o el PIN no es el de esa persona, el error es **el mismo** ("Usuario o clave incorrectos") y tarda lo mismo: no se revela si el correo o el celular existen. El bloqueo por intentos (5 fallos, 15 minutos) sigue contando sobre la cuenta a la que corresponde lo escrito. | sin revelar quién existe |
| S-246 | **"Olvidé mi PIN" y "Cambiar PIN con el código"** aceptan también correo o celular, con las mismas reglas de la iteración 40. | igual que entrar |
| S-247 | **Quien nació con Google no tiene PIN** y entra con el botón de Google. Desde **Mi cuenta** puede **crear su PIN** (6 dígitos, mismas reglas de siempre) sin escribir ningún PIN actual, porque ya está dentro con su sesión. Quien ya tiene PIN no puede "crear" otro así: lo cambia con su PIN actual o con "Olvidé mi PIN". | crear PIN opcional |
| S-248 | La respuesta de la sesión dice si el vecino **ya tiene PIN** (`tiene_pin`), para que la pantalla muestre o no "Crea tu PIN". | un dato más |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| LG-01 | `POST /api/sesion` con `tipo` vecino acepta en `usuario` un correo (contiene `@`), un celular (9 dígitos que empiezan con 9) o un número de cliente. | `INVALID_CREDENTIALS`, `ACCOUNT_LOCKED` |
| LG-02 | Un correo o celular que no existe da el mismo `INVALID_CREDENTIALS` que un PIN equivocado (S-245). | `INVALID_CREDENTIALS` |
| LG-03 | Los fallos por correo o celular suman al bloqueo de la cuenta correspondiente (S-245). | `ACCOUNT_LOCKED` |
| LG-04 | `POST /api/pin/olvide` y `POST /api/pin/restablecer` aceptan correo o celular en `usuario` (S-246) y siguen dando siempre la misma respuesta. | `INVALID_CODE`, `INVALID_PIN` |
| LG-05 | `POST /api/pin/crear {pin}` (vecino con sesión) crea el PIN de quien no tiene (S-247). | `LOGIN_REQUIRED`, `FORBIDDEN`, `PIN_ALREADY_SET`, `INVALID_PIN` |
| LG-06 | `GET /api/sesion` y la respuesta de entrar traen `tiene_pin` (S-248). | — |
| LG-07 | Entrar con número de cliente sigue funcionando igual que antes. | — |

## Criterios de aceptación (`tests/test_entrar_correo_celular.py`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| LG-A | Con el correo | correo de Ana en mayúsculas más su PIN | entra como Ana |
| LG-B | Con el celular | el celular de Ana más su PIN | entra como Ana |
| LG-C | Con el número | `101` más su PIN | entra como Ana (como antes) |
| LG-D | Quien no existe | correo y celular inventados | `INVALID_CREDENTIALS`, igual que con un PIN malo |
| LG-E | PIN de otra persona | correo de Ana y el PIN de otro vecino | `INVALID_CREDENTIALS`; no entra como nadie |
| LG-F | Bloqueo | 5 fallos con el correo de Ana | luego, con su PIN bueno por número, `ACCOUNT_LOCKED` |
| LG-G | Olvidé con el correo | `olvide` con el correo de Ana (verificado) | sale el código al correo; la respuesta es la de siempre |
| LG-H | Restablecer con el celular | código recibido más el celular | el PIN nuevo entra |
| LG-I | Crear PIN | vecino de Google sin PIN: `pin/crear` con `739104` | luego entra con su correo y ese PIN; `tiene_pin` pasa a verdadero |
| LG-J | Ya tiene PIN | vecino con PIN: `pin/crear` | `PIN_ALREADY_SET` y su PIN no cambia |
| LG-K | PIN flojo | `pin/crear` con `123456` | `INVALID_PIN` y no queda PIN |
| LG-L | `tiene_pin` | sesión de un vecino con PIN y de uno de Google | verdadero y falso |
| LG-M | Admin | admin entra con su usuario como siempre | sin cambios; un correo en el campo del admin no lo resuelve a un vecino |

## Pantalla

- El ingreso del vecino dice **"Correo, celular o número de cliente"** (acepta texto, no solo dígitos) y avisa: "Si te registraste con Google, entra con el botón de Google, no necesitas PIN."
- "¿Olvidaste tu PIN?" pide lo mismo.
- En **Mi cuenta**, quien no tiene PIN ve "Crea tu PIN (opcional)".

## Trazabilidad

| Regla / supuesto | Código | Prueba |
|---|---|---|
| LG-01, LG-07, S-244 | `customers.resolve_login`, `sesion_entrar` | LG-A, LG-B, LG-C |
| LG-02, LG-03, S-245 | `resolve_login` (lo que no existe va al número 0) y `auth.authenticate` | LG-D, LG-E, LG-F, LG-M |
| LG-04, S-246 | `pin_olvide` y `pin_restablecer` usan `resolve_login` | LG-G, LG-H |
| LG-05, S-247 | `auth.create_pin`, `POST /api/pin/crear` | LG-I, LG-J, LG-K |
| LG-06, S-248 | `me()` agrega `tiene_pin` | LG-L |
| Pantalla | `AuthDialog` (campo "Correo, celular o número de cliente", ayuda para Google, "Crea tu PIN"), `mappers.toAccount` | `mappers.test.ts` |

Pruebas de las propias pruebas (8 mutaciones a mano, revertidas, todas detectadas; una sobrevivió al inicio —un admin con el mismo texto que el número de un vecino— y se reforzó LG-M): correo sensible a mayúsculas, sin entrada por celular, un desconocido que no sigue el mismo camino que un número desconocido, el admin resuelto como vecino, crear PIN que pisa el existente, `tiene_pin` siempre verdadero, y olvidé o restablecer sin resolver el correo o el celular.

Se arregló de paso un fallo viejo de la pantalla: los campos del código y del PIN nuevo filtraban la letra "D" en vez de los caracteres que no son dígitos (`/D/g` en lugar de `/\D/g`), así que dejaban escribir letras.

Prueba real en producción: el vecino 106 entró con su correo, con su celular y con su número, y un correo inventado dio el mismo error de siempre.

Evidencia: `docs/evidencia/desarrollo/46-entrar-rojo.txt` y `46-entrar-verde.txt` (532 pruebas del motor, 14 nuevas; 85 del frontend, 2 nuevas).

# Iteración 48 · Datos de demostración y cuentas de depuración

## Requisito

Como equipo, queremos que `holayapa.app` muestre una semana completa con datos de ejemplo (zonas, vecinos, pedidos, una entrega y una liquidación) para la demostración al profesor, con cuentas de prueba de cada tipo y una cuenta de **admin global** que pueda ver la pantalla de cualquier persona para revisar cada parte del proceso. Como equipo, también queremos poder apagar todo eso antes de abrir de verdad.

## Por qué

El modo de demostración de siempre (`--demo`) vive solo en memoria, con una fecha fija de septiembre, y con claves conocidas que no se pueden usar en una web pública. Para el proyecto final, la web desplegada **es** la demostración, así que hacen falta datos de ejemplo guardados en su base, claves propias y la forma de revisar cada rol sin pedirle las claves a nadie.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-253 | **Base de demostración**: al crear una base nueva con `--sembrar-demo`, se carga la semana de demostración **ajustada a la semana en que se siembra**: la semana anterior entregada y liquidada, y la actual abierta con pedidos, con los mismos vecinos y zonas ficticios de siempre. La conciliación da 0. | semana actual |
| S-254 | **Reloj de demostración**: la base guarda el momento de la demo (el **miércoles a las 10:00** de la semana en que se sembró) y el motor lo usa como "ahora" para el negocio; así la semana está siempre abierta para probar. **La seguridad usa la hora real**: el bloqueo de 15 minutos tras 5 fallos y el vencimiento de las sesiones no siguen el reloj de demostración. | semana siempre abierta |
| S-255 | **Cuentas de prueba** con claves propias (variable `YAPA_DEMO_PINS`, p. ej. `101=123450,105=...`): Ana (101, admin de zona de Los Álamos), Marta (116, admin de zona de Arenales) y Carmen (105, vecina), más el admin de Yapa de siempre (`admin-yapa`). Las claves no se escriben en el código ni se muestran en pantalla. | tres tipos |
| S-256 | **Admin global de depuración** `debug-global` (clave en `YAPA_DEBUG_CLAVE`, solo se crea con `--sembrar-demo`): tiene el panel del equipo y además puede **"ver como"** cualquier vecino o admin de zona. No puede hacerse pasar por otro admin del equipo. | `debug-global` |
| S-257 | **"Ver como"**: abre una sesión como esa persona; la pantalla muestra siempre "Estás viendo Yapa como X" con un botón para volver; se puede hacer todo lo del negocio (pedir, pagar, confirmar) pero **no cambiar** su PIN, su correo ni su cuenta de Google. Cada "ver como" queda registrado con quién, como quién y cuándo. | sin tocar credenciales |
| S-258 | La base de demostración se puede **vaciar** borrando el archivo de la base: el siguiente arranque, sin `--sembrar-demo`, crea la base limpia del piloto. | se apaga borrando |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| DM-01 | `demo_store(now)` arma la semana de demostración con los ciclos y las fechas corridos a la semana de `now`; sin `now`, queda exactamente como antes (septiembre de 2026). | — |
| DM-02 | La semana anterior de la demostración queda **entregada, cerrada y liquidada**, y la actual **abierta** en el momento `now`, con pedidos verificados y otros por verificar. `audit.money_balance` da diferencia 0. | — |
| DM-03 | `seed_demo_base(ruta, now, pins, debug_clave)` crea la base con esos datos, el momento de la demo guardado, los PIN de las cuentas de prueba y a `debug-global`; sin PIN para alguna de las tres cuentas o con un PIN flojo, no crea nada. | `DEMO_PINS_REQUIRED`, `INVALID_PIN`, `INVALID_PASSWORD` |
| DM-04 | Si la base trae un momento de demostración guardado, el motor lo usa como reloj del negocio. | — |
| DM-05 | `create_api(..., security_clock=...)`: el bloqueo por intentos y la hora de las sesiones usan ese reloj (la hora real en el servidor); por omisión, el mismo del negocio, como hasta ahora. | — |
| DM-06 | `POST /api/admin/ver-como {usuario}` solo lo puede hacer un admin de depuración; abre la sesión de un vecino (o admin de zona) y `GET /api/sesion` dice `viendo_como` con quién lo hace. | `NOT_DEBUG_ADMIN`, `CUSTOMER_NOT_FOUND` |
| DM-07 | `POST /api/sesion/volver` (solo en una sesión de "ver como") devuelve a la sesión del admin global. | `NOT_VIEWING_AS` |
| DM-08 | En una sesión de "ver como" no se pueden cambiar el PIN, el correo ni la cuenta de Google. | `DEBUG_SESSION_READONLY` |
| DM-09 | Cada "ver como" y cada vuelta quedan en un registro con admin, persona, momento (hora real) y acción. | — |

## Criterios de aceptación (`tests/test_demostracion.py`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| DM-A | Sin `now` | `demo_store()` | igual que antes: `2026-W39` entregada y `2026-W40` abierta (las pruebas de siempre pasan) |
| DM-B | Corrida a otra semana | `demo_store(now=2026-10-21 10:00)` | la entregada es `2026-W42`, la abierta `2026-W43`; `is_open(now)`; conciliación 0 |
| DM-C | Cuentas y roles | semilla con PIN de prueba | Ana y Marta administran sus zonas, Carmen es vecina; entran con su PIN; `admin-yapa` entra con su clave |
| DM-D | PIN faltante o flojo | sin PIN de Marta, o `123456` | no crea la base |
| DM-E | Se guarda y se recarga | sembrar, cargar la base | el momento de demostración y las cuentas siguen ahí; `demo_clock(store)` devuelve ese momento |
| DM-F | Seguridad con hora real | reloj del negocio fijo, `security_clock` que avanza 16 min | tras 5 fallos y 16 min el PIN bueno entra |
| DM-G | Ver como | `debug-global` pide ver como 101 | `GET /api/sesion` da usuario 101 y `viendo_como`; un admin normal recibe `NOT_DEBUG_ADMIN`; un vecino, 403 |
| DM-H | Volver | `sesion/volver` | la sesión vuelve a ser `debug-global`; sin "ver como" da `NOT_VIEWING_AS` |
| DM-I | Credenciales bloqueadas | en "ver como": cambiar PIN, correo, Google | `DEBUG_SESSION_READONLY` y nada cambia |
| DM-J | Registro | un "ver como" y su vuelta | dos líneas en el registro de depuración |
| DM-K | Quien no existe | ver como 99999 | `CUSTOMER_NOT_FOUND`, sigue la sesión del admin global |

## Trazabilidad

| Regla / supuesto | Código | Prueba |
|---|---|---|
| DM-01, DM-02, S-253 | `demo.demo_store(now)` (ciclos y fechas corridos a la semana de `now`) | DM-A, DM-B (2) |
| DM-03, S-255, S-256 | `demo.seed_demo_base`, `parse_demo_pins`; opción `--sembrar-demo` en `web/__main__.py` | DM-C, DM-D, y que no pise una base existente |
| DM-04, S-254 | `store.demo_now`, `demo.demo_clock`, `web/__main__.py` lo usa como reloj del negocio | DM-E |
| DM-05, S-254 | `create_api(security_clock=...)` en el bloqueo por intentos y en la vida de las sesiones | DM-F (3) |
| DM-06, DM-07, S-256, S-257 | `ver_como`, `sesion_volver`, `me()` con `viendo_como` y `puede_ver_como` | DM-G (4), DM-H |
| DM-08, S-257 | guardia `credential_paths` en `dispatch` | DM-I (2) |
| DM-09 | `store.debug_log` | DM-J, DM-K y que el registro sobreviva a guardar y cargar |
| Pantalla | botón "Ver como" en Vecinos del panel (`AdminPanel`), aviso fijo y "Volver a mi cuenta" (`App`) | `mappers.test.ts` |

Pruebas de las propias pruebas (9 mutaciones a mano, revertidas): 8 detectadas. La que sobrevivió ("sin comprobar los PIN" dentro de `seed_demo_base`) es un caso equivalente, no un hueco: `auth.set_pin` revisa el PIN antes de guardar la base, así que el resultado es el mismo. Las detectadas: la seguridad con el reloj del negocio, cualquier admin que ve como, sin registro de depuración, credenciales sin proteger, volver sin comprobar, la semana sin correr, pisar una base existente, y aceptar a quien no existe.

Prueba real en producción: la base se respaldó (`yapa-vps/respaldos`), se borró y se sembró; `/api/estado` dice `2026-W43` abierto a las 10:00 de hoy; Ana (101) y Marta (116) entran como admin de zona, Carmen (105) como vecina, `admin-yapa` como equipo y `debug-global` como equipo con "ver como"; el admin global vio como Marta y volvió. Las claves están en `CREDENCIALES-YAPA.txt` y en `~/.yapa-cuentas-demo.txt`, fuera del repositorio.

Evidencia: `docs/evidencia/desarrollo/48-demostracion-rojo.txt` y `48-demostracion-verde.txt` (557 pruebas del motor, 20 nuevas; 93 del frontend, 1 nueva).

## Fuera de esta iteración (anotado)

- **Registro abierto con ubicación y aprobación del admin de zona** (idea del dueño, 21/10): cualquiera se registra, comparte su ubicación (el navegador pide permiso), solo entra a zonas a menos de 300 m, y el admin de la zona lo aprueba; la invitación queda como atajo que da beneficios a quien invita. Es la iteración 50 y reemplaza el supuesto S-236.
- Cuentas de proveedor y de la gestión de camiones, cuando existan esas pantallas.

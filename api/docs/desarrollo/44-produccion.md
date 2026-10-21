# Iteración 44 · Lista para producción

## Requisito

Como equipo, queremos poder dejar Yapa corriendo en un servidor propio para que los vecinos la abran desde su celular, sin que cualquiera pueda entrar como administrador ni se pierdan datos al reiniciar. Hoy el motor solo sirve para demo: crea sus propias claves conocidas, atiende una petición a la vez y solo escucha en la propia máquina.

## Por qué

Para el proyecto final se desplegará en un servidor (una máquina Windows prestada). Las credenciales de demo (`admin-yapa` / `yapa-admin-2026`, PIN `482915`) están escritas en el código y en la documentación: en un servidor abierto, cualquiera entraría como administrador. Esta iteración cierra eso y deja lo mínimo para operar: un administrador real, cookie segura, un chequeo de salud y servir la web ya construida desde el mismo motor.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-228 | **Arrancar con `--base` es "modo servidor"**. En ese modo **no se crean credenciales de demo** (ni PIN de vecinos ni el administrador de demo). Sin `--base` y sin `--demo` (desarrollo en la propia máquina) todo sigue como hoy. | demo solo local |
| S-229 | **El administrador real se define con variables de entorno** `YAPA_ADMIN_USUARIO` y `YAPA_ADMIN_CLAVE` al arrancar en modo servidor (la clave se guarda con sal y hash, nunca en claro, y no se imprime). Si la base ya tiene un administrador con clave, las variables son opcionales; si no la tiene y faltan, el motor **no arranca** y dice qué falta. La longitud mínima de la clave es la de siempre (S-70). | variables de entorno |
| S-230 | **Cookie segura**: si `YAPA_PUBLIC_URL` empieza con `https://`, la cookie de sesión lleva `Secure` (solo viaja por HTTPS). Con `http://` o sin la variable, igual que hoy. | Secure con https |
| S-231 | **Escuchar fuera de la propia máquina** se pide con `--escuchar 0.0.0.0` (por defecto `127.0.0.1`, como hoy). Escuchar fuera **exige `--base`**: un servidor abierto nunca arranca con datos de demo. | `--escuchar` |
| S-232 | **Varias peticiones a la vez**, de una en una por dentro: el servidor atiende cada conexión en su propio hilo, pero el motor ejecuta una petición a la vez (cerrojo global), porque el almacén no está hecho para hilos. Un cliente lento ya no bloquea a los demás. | cerrojo global |
| S-233 | **Chequeo de salud**: `GET /salud` responde `{"ok": true}` sin sesión y sin ningún dato. Sirve para que quien opere el servidor sepa si el motor está vivo. | `/salud` |
| S-234 | **El motor sirve la web ya construida** (`npm run build`, carpeta `dist`) con `--estaticos <carpeta>`. Lo que no es `/api/` ni `/salud` se sirve de ahí; las rutas desconocidas devuelven `index.html` (la web maneja sus propias rutas). Así la web y la API comparten dirección y la cookie funciona. Solo `GET` y `HEAD`. | `--estaticos` |
| S-235 | Las respuestas de archivos llevan `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` y `Referrer-Policy: strict-origin-when-cross-origin`. `index.html` no se guarda en caché; los demás archivos, una hora. | cabeceras mínimas |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| PR-01 | En modo servidor (S-228) no se crea ninguna credencial de demo: no existe `admin-yapa` con la clave conocida ni vecinos con PIN conocido. | — |
| PR-02 | En modo servidor, con `YAPA_ADMIN_USUARIO` y `YAPA_ADMIN_CLAVE`, ese usuario entra con esa clave (S-229). Sin la variable y sin administrador con clave en la base, no arranca. | `ADMIN_NOT_CONFIGURED` |
| PR-03 | Una clave de administrador de menos de 10 caracteres se rechaza (S-70). | `INVALID_PASSWORD` |
| PR-04 | Escuchar en una dirección que no sea `127.0.0.1` sin `--base` se rechaza (S-231). | `UNSAFE_LISTEN` |
| PR-05 | Con `YAPA_PUBLIC_URL` en `https://`, la cookie de sesión lleva `Secure`, al entrar y al salir (S-230). Sin eso, no la lleva. | — |
| PR-06 | `GET /salud` devuelve 200 y `{"ok": true}` sin sesión; no devuelve datos del negocio. | — |
| PR-07 | `--estaticos`: `GET /` devuelve `index.html`; un archivo existente se entrega con su tipo; una ruta desconocida **sin extensión** devuelve `index.html`; un archivo **con extensión que no existe** (por ejemplo `/assets/falta.js`) devuelve 404 y no se disfraza de página; `/api/...` sigue yendo a la API (S-234). | — |
| PR-08 | **Un archivo fuera de la carpeta nunca se entrega**: `/../x`, `/%2e%2e/x` y rutas con `\` o con bytes nulos dan 404, **tengan o no extensión** (`/../x` no devuelve la portada). | — |
| PR-09 | Un método que no sea `GET` o `HEAD` sobre un archivo estático devuelve 405. | — |
| PR-10 | Las respuestas de archivos llevan las cabeceras de S-235. | — |
| PR-11 | Dos peticiones simultáneas no se ejecutan a la vez dentro del motor (S-232). | — |

## Criterios de aceptación (`tests/test_produccion.py`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| PR-A | Sin demo en modo servidor | tienda nueva, `prepare_credentials(store, env con admin, demo=False)` | no hay `("admin", "admin-yapa")` ni vecinos con credencial; sí el admin del entorno |
| PR-B | El admin real entra | usuario `jefa-yapa`, clave de 12 caracteres | `auth.authenticate` devuelve `jefa-yapa`; con otra clave, `INVALID_CREDENTIALS` |
| PR-C | Falta el admin | tienda sin credenciales y entorno vacío | `ADMIN_NOT_CONFIGURED` |
| PR-D | Ya hay admin en la base | tienda con admin con clave y entorno vacío | no falla y no cambia la clave |
| PR-E | Clave corta | clave de 5 caracteres | `INVALID_PASSWORD` |
| PR-F | Escuchar fuera sin base | `check_listen("0.0.0.0", base=None)` | `UNSAFE_LISTEN`; con base o con `127.0.0.1`, sin error |
| PR-G | Cookie segura | `create_api(..., secure_cookie=True)`: entrar y salir | `Set-Cookie` contiene `Secure` en ambos; con `False`, en ninguno |
| PR-H | Salud | `GET /salud` sin sesión | 200, `{"ok": true}` |
| PR-I | Web estática | carpeta con `index.html` y `assets/a.js` | `/` y `/ruta/inventada` dan `index.html`; `/assets/a.js` da el archivo con tipo JavaScript; `/assets/falta.js` da 404; `/api/sesion` sigue en la API |
| PR-J | Fuera de la carpeta | `/../secreto.txt`, `/../secreto` (sin extensión), `/%2e%2e/secreto.txt`, `/..%5csecreto.txt` | 404 y no aparece el contenido del archivo secreto ni la portada |
| PR-K | Solo lectura | `POST /` | 405 |
| PR-L | Cabeceras | `GET /` | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Cache-Control: no-cache` para `index.html` |
| PR-M | Cerrojo | dos hilos llaman a una aplicación lenta envuelta con `locked` | nunca hay dos dentro a la vez |

## Fuera de esta iteración (anotado)

- Las **solicitudes de unión de zona y de PIN** siguen en memoria: se pierden al reiniciar el motor. Se anotó en la lista de mejoras.
- **HTTPS**: el motor habla HTTP. El certificado lo pone un servidor delante (por ejemplo Caddy) cuando se abra a internet. Sin eso, la cookie `Secure` no se activa.
- Límite de intentos de PIN por dirección IP.

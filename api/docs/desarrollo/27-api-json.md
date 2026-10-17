# Iteración 27 · API JSON para el frontend de Kalos

## Requisito

Como equipo, queremos que la app React de Kalos (`src/` en `kaloslazo/Yapa`) use **las mismas reglas** que este motor, para tener una sola implementación del negocio con sus pruebas, y no dos copias que se separen.

## Por qué

- Decisión del equipo (17/10/2026): el frontend de Kalos es la cara de Yapa y este motor es el backend. Se deja Appwrite.
- La app de Kalos reimplementó en TypeScript las reglas de la iteración 2. Le faltan zonas de vecinos, armado y entrega con foto, reclamos, ahorro frente al mercado, conciliación, métricas y el código de pago generado (S-150). Todo eso ya está aquí, con pruebas.
- La API es **otro adaptador**, igual que la web HTML: no tiene reglas de negocio, solo llama a los casos de uso y devuelve JSON.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-153 | La API vive en `/api/...` del mismo servidor. En desarrollo, Vite reenvía `/api` al puerto 8000, así navegador y API comparten origen y la cookie de sesión. | — |
| S-154 | Los montos van como texto con dos decimales (`"61.00"`) para no perder céntimos con números de coma flotante. Las cantidades van como texto (`"0.25"`). | — |
| S-155 | La sesión de la API usa la misma cookie `HttpOnly` y `SameSite=Lax` de la iteración 10. Todo `POST` debe traer la cabecera `X-Yapa-CSRF` con el token que entrega `GET /api/sesion` (AC-06). | — |
| S-156 | Un error de negocio responde 422 con `{"error": {"codigo": ..., "mensaje": ...}}`. Sin sesión: 401. Sin permiso: 403. Ruta inexistente: 404. | — |
| S-157 | La API da el rol del usuario: `vecino`, `admin_zona` (vecino que administra una zona) o `admin` (equipo Yapa). El admin de zona es un vecino con permisos extra sobre su zona (iteración 5); no es otro tipo de cuenta. | — |

## Reglas

| Regla | Comportamiento |
|---|---|
| API-01 | `GET /api/estado` da el ciclo actual, si está abierto, el cierre y las ventanas de entrega. `GET /api/catalogo` da los productos activos del ciclo con precio máximo, tramos, avance hacia el siguiente tramo y precios de referencia vigentes. `GET /api/zonas` da las zonas con su estado, grupo y ubicación. Todo sin sesión. |
| API-02 | `POST /api/sesion` entra (vecino con número y PIN; admin con usuario y contraseña), `GET /api/sesion` dice quién es, su rol (S-157), su saldo y el token CSRF, y `DELETE /api/sesion` sale. |
| API-03 | Vecino: `POST /api/cotizar` (carrito con nombres, total, ahorro frente al supermercado y saldo), `POST /api/pedidos` (registra con código de pago generado, S-150), `GET /api/mis-pedidos` (pedidos con estado, avance, si se puede cancelar, lo devuelto y la comparación), `POST /api/pedidos/<n>/cancelar`, `POST /api/saldo/devolucion`, `POST /api/pin`. |
| API-04 | Reclamos del vecino: `GET /api/reclamos` (artículos que puede reclamar y sus reclamos) y `POST /api/reclamos` (con foto como archivo, S-151). |
| API-05 | Zona: `GET /api/mi-zona` y `POST /api/zonas`, `/api/zonas/<id>/unirme`, `/activar`, `/unir`, `/separar`, `/transferir`, `/api/solicitudes/<n>/aceptar` y `/rechazar`, con las reglas de la iteración 5. |
| API-06 | Admin Yapa: `GET /api/admin/resumen` (indicadores, pagos por verificar, grupos frente al mínimo), `POST /api/admin/pedidos/<n>/verificar`, `POST /api/admin/ciclos/<c>/liquidar`, `GET /api/admin/armado`, `POST /api/admin/bolsas`, `/entregas`, `/entregas-fallidas`, `GET` y `POST` de reclamos, devoluciones, conciliación, métricas, catálogo, referencias y vecinos. |
| API-07 | Los permisos son los de la web (AC-04, AC-05): el vecino solo ve y toca lo suyo; las rutas `/api/admin` son solo del admin de Yapa. |

## Criterios de aceptación

Hora fija: miércoles 16/09/2026 a las 10:00 (2026-W38), catálogo base del piloto, PIN de Ana (101) `482915`.

- **API-A · Público.** `GET /api/catalogo` → 200, papa amarilla con `precio_max` `"4.03"` y siguiente tramo desde `"100"` a `"3.79"`; sin plátano. `GET /api/estado` → ciclo `2026-W38`, abierto. `GET /api/zonas` incluye `Z-LINCE-01`.
- **API-B · Sesión.** Ana entra → 200, `rol` `vecino`, nombre `Ana Torres`, `csrf` presente y cookie `HttpOnly`. Con PIN equivocado → 422 `INVALID_CREDENTIALS`. Después de `DELETE /api/sesion`, `GET /api/mis-pedidos` → 401.
- **API-C · CSRF.** Un `POST /api/pedidos` sin la cabecera `X-Yapa-CSRF` → 403.
- **API-D · Comprar.** `POST /api/cotizar` con 5 kg de papa amarilla, 10 de papa blanca y 10 de cebolla roja → total `"61.00"` y los nombres. `POST /api/pedidos` con el mismo carrito y `YAPE` → 201, pedido 1, `codigo_pago` `YP-2026W38-101-XXXX`, `a_yapear` `"61.00"`. Un carrito bajo el mínimo → 422 `SUBTOTAL_BELOW_MINIMUM`.
- **API-E · Mis pedidos y cancelar.** `GET /api/mis-pedidos` muestra el pedido 1 `REGISTRADO`, `cancelable` verdadero. Tras verificar el pago y cancelar a saldo, el pedido queda `CANCELADO_POR_CLIENTE` y el saldo es `"61.00"`.
- **API-F · Admin.** `GET /api/admin/resumen` sin ser admin → 403. Como admin, lista el pedido por verificar; tras `POST /api/admin/pedidos/1/verificar`, ya no está.
- **API-G · Semana completa por la API.** Con 8 vecinos de Jesús María que piden y pagan, el admin arma las bolsas, entrega con foto y liquida → los pedidos quedan `LIQUIDADO` y `GET /api/admin/conciliacion` da diferencia `"0.00"`.
- **API-H · Zona.** Un vecino crea una zona en Lince y queda como su admin (`rol` `admin_zona`); `GET /api/mi-zona` lo dice. Otro vecino a 100 m se une. Transferir el rol a ese vecino → el primero vuelve a `vecino`.
- **API-I · Errores.** Ruta inexistente → 404 en JSON; error de negocio → 422 con `codigo` y `mensaje`.

# Iteración 12 · Pantallas web para zonas, armado, entrega, reclamos, colchón y métricas

## Requisito

Como vecino, quiero crear la zona de mi edificio o unirme a una cercana, reclamar un artículo que me llegó mal y pedir de vuelta mi saldo, todo desde el celular.

Como vecino admin de una zona, quiero activarla cuando la portería acepta recibir, unirla con la zona de al lado y pasarle el rol a otro vecino.

Como administrador de Yapa, quiero registrar el armado (foto por bolsa) y la entrega en portería, aprobar o rechazar reclamos, manejar el colchón de reposición y ver un tablero con las métricas del piloto, sin usar la consola.

## Por qué ahora

Las iteraciones 3, 5, 7 y 8 ya tienen reglas y pruebas, pero solo se podían usar desde el código. La web de las iteraciones 9 y 10 cubría el pedido, el pago y la liquidación.

## Decisiones que se aplican

- **La web es solo un adaptador** (iteración 9). Cada pantalla llama a un caso de uso que ya existe:
  - `zones.py`: `create_zone`, `activate_zone`, `join_zone`, `request_merge`, `accept_merge`, `leave_group`, `transfer_admin`;
  - `fulfillment.py`: `pack_bag`, `deliver_zone`;
  - `claims.py`: `file_claim`, `review_claim`;
  - `buffer.py`: `add_to_buffer`, `use_buffer`;
  - `metrics.py`: `order_margins`, `margin_alerts`, `delivered_savings`, `repurchase_week4`;
  - `wallet.request_withdrawal`.

  Las decisiones de negocio (plazos, topes, quién puede) las toma el caso de uso, no la web.
- **Acceso (iteración 10):**
  - Las pantallas del vecino piden sesión de vecino, y el actor es siempre el de la sesión (AC-04).
  - Las del administrador piden sesión de administrador (AC-05).
  - Todo POST lleva el token CSRF (AC-06).
  - El usuario del administrador es el "personal de Yapa" que exigen el armado, la entrega, el colchón y la revisión de reclamos (S-40).
- **Se mantienen:**
  - WB-07: todo texto se escapa;
  - WB-08: 404, 405 y 422 con el código del error;
  - WB-09: viewport y una sola columna.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-72 | Las fotos (bolsa, entrega, reclamo) se registran como **referencia de texto**: la ruta del archivo o su URL, escrita en el formulario. **Subir archivos queda fuera de alcance**, porque necesita recibir archivos y guardarlos en algún lado. La referencia se muestra como texto escapado, **nunca como enlace ni como imagen**, para que nadie pueda meter un enlace `javascript:`. | texto |
| S-73 | Las acciones de admin de zona son activar, pedir y aceptar la unión, separarse y transferir el rol. Las hace **el vecino que es admin de la zona**, desde su sesión de vecino (C-07). El administrador de Yapa no las hace por la web. | — |
| S-74 | Para crear una zona, el vecino ya tiene que tener su ubicación registrada. Esta iteración **no** agrega cómo registrarla (ver huecos): si falta, se muestra `LOCATION_REQUIRED`. El punto de recepción se escribe como latitud y longitud en números decimales. | — |
| S-75 | Las zonas cargadas antes de la iteración 5 no tienen ubicación registrada. Una zona así **no recibe vecinos nuevos ni se une a un grupo**: responde `LOCATION_REQUIRED`. Antes el código fallaba con un error interno. Es el único cambio fuera de la web. | — |
| S-76 | La web convierte el texto del formulario antes de llamar al caso de uso. Si el dato no tiene el formato esperado, responde `INVALID_INPUT` (422) sin caerse. Es un control de formato, no una regla de negocio. Los formatos esperados son:<ul><li>número de pedido, reclamo o cliente: un entero;</li><li>coordenada: un número finito;</li><li>monto: soles con hasta 2 decimales;</li><li>artículo del reclamo: `pedido:producto`.</li></ul> | — |
| S-77 | Las pantallas del administrador usan el **ciclo actual** (hora de Lima). Armado y métricas aceptan `?ciclo=AAAA-Wnn` para ver otro ciclo. El colchón usa el catálogo del ciclo actual. | — |
| S-78 | El tablero de métricas es por ciclo:<ul><li>Si el ciclo no está liquidado, responde 422 con `CYCLE_NOT_SETTLED`, como las demás pantallas.</li><li>La recompra toma ese ciclo como cohorte y mira 3 semanas después (N + 3).</li><li>Si la recompra todavía no se puede calcular (N + 3 sin liquidar o nadie compró por primera vez en N), su sección muestra el motivo y el resto del tablero se ve igual.</li></ul> | — |
| S-79 | Para reclamar, el vecino elige el artículo de una lista con las líneas de **sus pedidos entregados**. La lista es solo una ayuda: el caso de uso vuelve a validar todo (RC-01..RC-06). En "Mis reclamos" solo ve los suyos. | — |
| S-80 | El administrador revisa los reclamos **uno por uno** desde la lista de pendientes, con los botones "Aprobar" o "Rechazar" (S-45). Los revisados se muestran con su resultado y el monto devuelto. | — |

## Reglas

### Vecino

| Regla | Comportamiento | Respuesta |
|---|---|---|
| OP-01 | `GET /zona` muestra:<ul><li>la zona del vecino: nombre, distrito, si está activa o le falta quien reciba, y su grupo;</li><li>las zonas existentes;</li><li>los formularios para crear una zona (nombre, distrito, latitud, longitud) y para unirse a otra.</li></ul>Si el vecino es admin de su zona, también ve:<ul><li>activar (tipo de recepción y contacto);</li><li>pedir la unión con otra zona;</li><li>las solicitudes de unión que recibió, con el botón "Aceptar";</li><li>separarse del grupo;</li><li>transferir el rol.</li></ul> | 200 |
| OP-02 | Cada ruta llama a su caso de uso, con el vecino de la sesión como actor (S-73):<ul><li>`POST /zona/crear`: `create_zone`;</li><li>`POST /zona/unirse`: `join_zone`;</li><li>`POST /zona/activar`: `activate_zone`;</li><li>`POST /zona/unir`: `request_merge`;</li><li>`POST /zona/aceptar`: `accept_merge`;</li><li>`POST /zona/separar`: `leave_group`;</li><li>`POST /zona/transferir`: `transfer_admin`.</li></ul> | 200, o 422 con el error del caso de uso o `INVALID_INPUT` (S-76) |
| OP-03 | `GET /reclamos` muestra los reclamos del vecino (artículo, cantidad, motivo, estado, monto devuelto) y un formulario con el artículo, la cantidad, el motivo ("Faltó" o "Llegó dañado") y la foto (S-72, S-79). `POST /reclamos` llama a `file_claim` con el cliente de la sesión. | 200, o 422 |
| OP-04 | `POST /cuenta/devolucion` llama a `request_withdrawal` con el monto pedido. `/cuenta` muestra el formulario, el saldo que queda y la devolución pendiente. | 200, o 422 |

### Administrador

| Regla | Comportamiento | Respuesta |
|---|---|---|
| OP-05 | `GET /admin/armado` muestra dos cosas del ciclo (S-77):<ul><li>los pedidos que se atienden, con sus bolsas y fotos y un formulario para registrar otra bolsa;</li><li>las zonas con pedidos atendidos, cada una con su estado de entrega y el formulario de entrega (foto y nombre de quien recibe).</li></ul>`POST /admin/bolsa` llama a `pack_bag` y `POST /admin/entrega` llama a `deliver_zone`, con el administrador de la sesión como actor. | 200, o 422 |
| OP-06 | `GET /admin/reclamos` lista los pendientes (pedido, cliente, artículo, cantidad, motivo, foto) con "Aprobar" y "Rechazar", y después los ya revisados. `POST /admin/reclamos/revisar` llama a `review_claim` (S-80). | 200, o 422 |
| OP-07 | `GET /admin/colchon` muestra lo guardado (producto, cantidad, valor), el valor total y el tope. `POST /admin/colchon/agregar` llama a `add_to_buffer` y `POST /admin/colchon/usar` llama a `use_buffer`. | 200, o 422 |
| OP-08 | `GET /admin/metricas` muestra, para el ciclo (S-77, S-78):<ul><li>el margen de cada pedido liquidado, marcando los negativos;</li><li>el ahorro entregado (por volumen, por envío y total);</li><li>la recompra en la semana 4 contra la meta del 50 %.</li></ul> | 200; 422 si el ciclo no está liquidado |

### Transversales

| Regla | Comportamiento | Respuesta |
|---|---|---|
| OP-09 | Las rutas nuevas del vecino piden sesión de vecino y las del administrador, sesión de administrador (AC-04, AC-05). Todo POST lleva el token CSRF (AC-06). Si no hay sesión, redirige a `/entrar`; si el rol no corresponde, 403; si falta el token, 403 y no se cambia nada. | 303 / 403 |
| OP-10 | WB-07, WB-08 y WB-09 se cumplen en todas las pantallas nuevas. Las fotos se muestran como texto (S-72). | 404 / 405 / 422 |
| OP-11 | Una zona sin ubicación no recibe vecinos nuevos ni entra a un grupo (S-75). | `LOCATION_REQUIRED` |

## Criterios de aceptación

Datos de partida:

- Catálogo base del piloto y 8 pedidos verificados en Z-JM-01 (la canasta de las pruebas de liquidación), de los clientes 1001 a 1008, que son los pedidos 1 a 8.
- La hora del servidor avanza según el caso:
  - miércoles 16/09 10:00 (ciclo 2026-W38 abierto);
  - viernes 18/09 10:00 (armado);
  - sábado 19/09 09:00 (entrega);
  - domingo 20/09 08:00 (reclamo).
- Para las zonas se usa el punto (−12.0850, −77.0350) y vecinos con ubicación. Como en las pruebas de zonas, 0.0009° de latitud son unos 100 m.

### Vecino

- **OA-01 · Crear zona.** El vecino 3001, con ubicación, crea "Torre Sol" en Lince.
  - Queda la zona Z-001 con él como admin, y él pasa a ser vecino de esa zona.
  - `/zona` muestra "Torre Sol" y "Falta quien reciba".
  - Un distrito fuera del piloto → 422 con `DISTRICT_NOT_IN_PILOT`.
  - → OP-01, OP-02, ZN-01
- **OA-02 · Activar zona.** El 3001 activa Z-001 con portería "Sr. Ramos": la zona queda activa y `/zona` muestra "Activa". Otro vecino que intenta activar Z-001 → 422 con `NOT_ZONE_ADMIN`, y el contacto no cambia. → OP-02, ZN-02, S-73
- **OA-03 · Unirse.** Con Z-001 creada:
  - un vecino a 100 m se une y su zona pasa a Z-001;
  - uno a 400 m → 422 con `OUTSIDE_ZONE_RADIUS`;
  - unirse a Z-LINCE-01, que no tiene ubicación → 422 con `LOCATION_REQUIRED`, sin error interno.
  - → OP-02, OP-11, ZN-03, S-75
- **OA-04 · Unir grupos, separarse y transferir.** El 3001 (Z-001) y el 3003 (Z-002, a 300 m) crean sus zonas.
  - El 3001 pide unirse a Z-002. El 3003 ve la solicitud en `/zona` y la acepta: las dos zonas quedan en el grupo G-Z-002.
  - El 3001 se separa y Z-001 vuelve a G-Z-001.
  - Pedir la unión con Z-LINCE-01 → 422 con `LOCATION_REQUIRED`.
  - El 3001 transfiere el rol a un vecino de su zona: ese vecino queda como admin.
  - → OP-01, OP-02, ZN-04..ZN-07
- **OA-05 · Datos mal formados en zonas.** Crear una zona con latitud `abc` o `nan`, o transferir el rol a `abc` → 422 con `INVALID_INPUT`, y no se crea ninguna zona. → S-76, WB-08
- **OA-06 · Pedir devolución del saldo.** El 1001 tiene S/ 20.00 de saldo y pide S/ 12.50:
  - `/cuenta` muestra "Saldo: S/ 7.50" y la devolución pendiente de S/ 12.50;
  - pedir S/ 30 → 422 con `INSUFFICIENT_BALANCE`;
  - pedir `0` → 422 con `INVALID_AMOUNT`;
  - pedir `abc` o `0.001` → 422 con `INVALID_INPUT`.
  - → OP-04, BS-12, S-76
- **OA-07 · Reclamar un artículo.** Con la zona entregada y el ciclo liquidado, el domingo a las 08:00:
  - el 1001 ve en `/reclamos` la opción "Cebolla roja" de su pedido 1;
  - reclama 1 kg de cebolla dañada con su foto: queda el reclamo 1, `PENDIENTE`, a su nombre;
  - el 1002 intenta reclamar sobre el pedido 1 → 422 con `ORDER_NOT_FOUND`;
  - un artículo `xx` → 422 con `INVALID_INPUT`.
  - → OP-03, RC-01..RC-06, S-79

### Administrador

- **OA-08 · Armado.**
  - El viernes, `/admin/armado` lista los 8 pedidos. Al registrar una bolsa del pedido 1 con la foto `fotos/p1-b1.jpg`, queda la bolsa 1 hecha por `admin-yapa` y la página muestra la foto.
  - Sin foto → 422 con `PHOTO_REQUIRED`.
  - El miércoles, con el ciclo abierto → 422 con `CYCLE_STILL_OPEN`.
  - → OP-05, AR-01..AR-05
- **OA-09 · Entrega.**
  - Con 7 de los 8 pedidos armados, entregar Z-JM-01 → 422 con `ORDERS_NOT_PACKED`.
  - Con los 8 armados, el sábado se entrega a "Sr. Ramos" con foto: queda la entrega de Z-JM-01 con los 8 pedidos, y `/admin/armado` la muestra como entregada.
  - → OP-05, EN-01..EN-05
- **OA-10 · Revisar reclamos.** Con el reclamo 1 del OA-07:
  - `/admin/reclamos` lo lista como pendiente;
  - al aprobarlo, queda `APROBADO` por S/ 2.02 (80 kg de cebolla → S/ 1.80 × 1.12 = S/ 2.016, redondeado a favor del cliente) y el saldo del 1001 sube S/ 2.02;
  - revisarlo otra vez → 422 con `CLAIM_ALREADY_REVIEWED`;
  - un segundo reclamo rechazado queda `RECHAZADO` y el saldo no cambia.
  - → OP-06, RV-01..RV-05, S-80
- **OA-11 · Colchón.**
  - Agregar 10 limpiatodos → valor S/ 79.00 de un tope de S/ 500.00.
  - Papa amarilla → 422 con `PERISHABLE_NOT_ALLOWED`.
  - 60 limpiatodos más (S/ 553 en total) → 422 con `BUFFER_LIMIT_EXCEEDED`.
  - Usar 4 → quedan 6, con un valor de S/ 47.40.
  - → OP-07, CO-01..CO-05
- **OA-12 · Tablero de métricas.**
  - Con W38 liquidado, `/admin/metricas?ciclo=2026-W38` muestra:
    - el margen S/ 5.64 del pedido 1 (MT-A);
    - el ahorro total de S/ 26.88 (MT-D);
    - en la sección de recompra, el motivo `CYCLE_NOT_SETTLED`, porque W41 no está liquidado. La página responde 200.
  - Con W39 sin liquidar → 422 con `CYCLE_NOT_SETTLED`.
  - → OP-08, S-78

### Transversales

- **OA-13 · Acceso.**
  - Sin sesión, `/zona` → 303 a `/entrar`.
  - Un vecino en `/admin/armado` → 403, y un administrador en `/zona` → 403.
  - Un POST a `/reclamos` sin token → 403, y no se crea ningún reclamo.
  - → OP-09, AC-04..AC-06
- **OA-14 · Rutas y escape.**
  - `/admin/no-existe` → 404 y `GET /zona/crear` → 405.
  - Una zona llamada `<script>alert(1)</script>` aparece escapada en `/zona`.
  - Una bolsa con la foto `javascript:alert(1)` aparece como texto en `/admin/armado`, sin ningún `href="javascript:`.
  - → OP-10, WB-07, WB-08, S-72
- **OA-15 · Celular.** `/zona`, `/reclamos`, `/admin/armado`, `/admin/reclamos`, `/admin/colchon` y `/admin/metricas` tienen `<meta name="viewport"`. → OP-10, WB-09

## Fuera de alcance

- **Subir archivos de foto** (S-72).
- **Registrar la ubicación del vecino** (ver huecos).
- **Pantalla para que el administrador registre el pago de una devolución** (`mark_refund_paid`). El caso de uso existe, pero esta iteración no lo pidió.

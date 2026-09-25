# Iteración 9 · Interfaz web (vecino y administrador)

## Requisito

Como vecino, quiero entrar desde el celular, ver el catálogo de la semana con el precio máximo y cuánto falta para el siguiente descuento, cotizar, pagar mi pedido con Yape/Plin (o mi saldo) y ver mi saldo y mis pedidos.

Como administrador, quiero ver los pagos por verificar, verificarlos y liquidar el ciclo desde el navegador.

## Decisiones que se aplican

- **Entregable 1, §4.1:** Yapa es una **aplicación web responsiva**, sin app nativa.
- **C-02 / modelo del 24/09:** mostrar en vivo el precio máximo que se paga hoy y el avance hacia el siguiente tramo ("80 de 100 bolsas para el siguiente descuento"), dejando claro que la diferencia vuelve como saldo.
- **CLAUDE.md:** solo biblioteca estándar de Python (`wsgiref`, `html`, `urllib`). La web es un **adaptador**: no contiene reglas de negocio, solo llama a los casos de uso ya especificados.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-39 | En esta etapa **no hay inicio de sesión**: el vecino se identifica con su número de cliente. La autenticación queda para una iteración posterior. | — |
| S-40 | Las páginas de administración no tienen contraseña en esta etapa. Por eso **el servidor de demo solo escucha en la propia máquina** (`127.0.0.1`). | — |
| S-41 | Los datos viven en memoria mientras el servidor está prendido (repositorio en memoria). La persistencia es otra iteración. | — |
| S-42 | Para la demo se puede fijar la hora con `--ahora` (por ejemplo, un miércoles a las 10:00) para ver el ciclo abierto. Sin esa opción se usa la hora real de Lima. | — |

## Reglas

| Regla | Comportamiento | Respuesta |
|---|---|---|
| WB-01 | `GET /` muestra el ciclo actual (abierto o cerrado, con la hora de cierre) y el catálogo del ciclo: nombre, unidad, **precio máximo**, lo pedido hasta ahora entre todos y el siguiente tramo ("desde X baja a S/ Y"). Los productos inactivos no aparecen. | 200 |
| WB-02 | `POST /cotizar` con el cliente y las cantidades (`cant_<PRODUCTO>`) devuelve el detalle y el **total a yapear**. Los campos vacíos o en 0 se ignoran. | 200, o 422 con el error |
| WB-03 | `POST /pedidos` registra el pedido con medio, código de operación, monto y saldo a usar. Muestra el número de pedido y su estado. | 200, o 422 con el error |
| WB-04 | `GET /cuenta?cliente=N` muestra el saldo, los pedidos (estado y total) y los reembolsos pendientes del vecino. | 200; 404 si el cliente no existe |
| WB-05 | `POST /cuenta/cancelar` cancela un pedido del vecino con el destino elegido (medio de pago o saldo). | 200, o 422 con el error |
| WB-06 | `GET /admin` lista los pedidos del ciclo con pago por verificar. `POST /admin/verificar` verifica uno. `POST /admin/liquidar` liquida un ciclo y muestra el resumen (precio final por producto, estado y saldo de cada pedido). | 200, o 422 con el error |
| WB-07 | Todo texto que viene del usuario o de los datos se **escapa** antes de mostrarse (evita que alguien inyecte código en la página). | — |
| WB-08 | Un error de negocio se muestra con su mensaje en español y su código. Una ruta inexistente responde 404 y un método incorrecto responde 405. Un dato mal formado (cliente o cantidad no numérica) se muestra como error, sin que el servidor se caiga. | 422 / 404 / 405 |
| WB-09 | Todas las páginas son usables en el celular: tienen `viewport` y un diseño de una columna. | — |

## Criterios de aceptación

Hora fija: miércoles 16/09/2026 a las 10:00 (ciclo 2026-W38 abierto) y catálogo base del piloto.

- **WA-01 · Catálogo.** `GET /` → 200. Muestra "Papa amarilla" con precio máximo S/ 4.03 y "desde 100 kg baja a S/ 3.79". No muestra "Plátano de seda" (inactivo). → WB-01
- **WA-02 · Avance del tramo.** Después de registrar un pedido de 5 kg de papa amarilla, `GET /` muestra "5 de 100 kg". → WB-01
- **WA-03 · Cotizar.** Las cantidades del CA-01 dan "Total a yapear: S/ 59.51". → WB-02
- **WA-04 · Cotizar con error.** Un subtotal bajo el mínimo → 422, con el mensaje "Faltan S/" y el código `SUBTOTAL_BELOW_MINIMUM`. → WB-02, WB-08
- **WA-05 · Registrar.** El formulario completo con Yape y un código nuevo → "Pedido 1" en estado `REGISTRADO`. → WB-03
- **WA-06 · Registrar con error.** Un código de operación repetido → 422 con `PAYMENT_CODE_ALREADY_USED`. → WB-03
- **WA-07 · Mi cuenta.** Después de registrar, `/cuenta?cliente=101` muestra el pedido 1 y un saldo de S/ 0.00. Un cliente inexistente → 404. → WB-04
- **WA-08 · Cancelar desde la web.** Con el pago verificado, al cancelar con destino saldo, la cuenta muestra un saldo de S/ 59.51. → WB-05
- **WA-09 · Admin.** `GET /admin` lista el pedido por verificar. Al verificarlo, deja de estar en la lista. → WB-06
- **WA-10 · Liquidar desde la web.** Con 8 pedidos verificados en Jesús María, `POST /admin/liquidar` muestra el precio final por producto y los pedidos `LIQUIDADO`. → WB-06
- **WA-11 · Inyección de HTML.** Un cliente llamado `<script>alert(1)</script>` aparece escapado (`&lt;script&gt;`) en su cuenta. → WB-07
- **WA-12 · Rutas y datos malos.** `/no-existe` → 404; `GET /pedidos` → 405; `cliente=abc` → error mostrado, sin caída. → WB-08
- **WA-13 · Celular.** Todas las páginas incluyen `<meta name="viewport"`. → WB-09

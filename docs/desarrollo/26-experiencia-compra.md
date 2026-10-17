# Iteración 26 · Experiencia de compra: carrito, pedidos con botones y ahorro a la vista

## Requisito

Como vecino, quiero armar mi pedido como en una tienda (sumar y restar, ver mi carrito y cuánto ahorro), pagar en un paso claro, y ver mis pedidos con botones para cancelarlos, sin escribir números de pedido a mano.

Como administrador, quiero abrir el panel y ver de un vistazo cómo va la semana y qué tengo que hacer ahora.

## Por qué

- Revisión del equipo (17/10/2026) sobre la iteración 25: para cancelar hay que **escribir** el número de pedido; no hay carrito; Mi cuenta y el panel del admin se leen como formularios sueltos; y los mensajes importantes (cuánto ahorras, que el pedido quedó registrado) no se destacan.
- El ahorro es la razón para usar Yapa (C-01, C-02, iteraciones 22 y 23). Si no se ve, el vecino no lo siente.
- La web sigue siendo un **adaptador**: no cambia ninguna regla. Cancelar, cotizar, registrar, verificar y liquidar llaman a los mismos casos de uso, con los mismos errores.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-144 | El carrito del catálogo calcula en el navegador un total **aproximado** (cantidad × precio máximo). El total que vale es el de la página "Tu carrito", que calcula el servidor con las reglas de siempre. Sin JavaScript, el catálogo sigue funcionando con los campos de cantidad. | — |
| S-145 | El ahorro estimado del carrito compara contra el precio de supermercado vigente, solo en los productos que lo tienen, y se presenta como "aprox.". | — |
| S-146 | Al vecino se le muestran los estados con palabras ("Registrado", "Cancelado", "Liquidado"...), no con el código interno. El administrador sigue viendo el código en la liquidación, porque lo usa para operar. | — |
| S-147 | El botón de cancelar solo aparece en los pedidos que todavía se pueden cancelar (registrados y con el ciclo abierto, CE-02 y CE-03). Si igual llega una cancelación inválida, responde el error de siempre. | — |
| S-149 | Pedido del equipo (17/10/2026): **escribir lo menos posible**. Cuando las opciones son conocidas (ciclos, pedidos, zonas, vecinos), se eligen de una lista. Solo se escribe lo que no se puede elegir: PIN, montos, códigos de operación, nombres y fotos. Las explicaciones largas van en secciones desplegables o en tablas. | — |
| S-148 | En "Tu carrito", si el vecino tiene saldo, una casilla "Usar mi saldo" lo aplica hasta el total. El monto a yapear **no se escribe**: es el total menos el saldo usado. | — |
| S-150 | **Decisión de Carlos (17/10/2026):** el vecino no escribe el código de operación. Al registrar, Yapa genera un **código de pago** único (`YP-<semana>-<cliente>-<4 caracteres>`) y le dice al vecino cuánto yapear y que ponga ese código en el mensaje del Yape o Plin. El admin verifica buscando ese código (RP-15). Cambia el orden de la iteración 2: antes se pagaba y luego se registraba con el código; ahora se registra, se paga con el código y se verifica. El pedido queda `POR_VERIFICAR` igual que antes. | — |
| S-151 | Las fotos (reclamo, bolsa, entrega, entrega fallida) se **suben como archivo**, desde la cámara en el celular. Se guardan en la carpeta `fotos/` y el pedido guarda la ruta, como pedía S-72. Se sigue aceptando una ruta escrita (compatibilidad con las pruebas y la API). | — |
| S-152 | Al crear una zona, la latitud y la longitud se llenan con el botón "Usar mi ubicación" del navegador; el vecino no las escribe. | — |

## Reglas

| Regla | Comportamiento |
|---|---|
| EC-01 | El catálogo tiene botones − y + por producto que respetan el paso del producto, y una barra fija "Tu carrito" con artículos, total aprox., cuánto falta para el mínimo de S/ 50 y el ahorro aprox. frente al supermercado (S-144, S-145). El botón lleva a "Tu carrito". |
| EC-02 | "Tu carrito" (`POST /cotizar`) muestra cada producto **con su nombre**, el total a yapear destacado, el ahorro frente al supermercado si hay precios, y el formulario de pago con las cantidades ya incluidas (S-148). "Seguir comprando" vuelve al catálogo. |
| EC-03 | Al registrar, la confirmación saluda al vecino por su nombre, muestra el número de pedido y lo que pasa después (verificación del pago, compra, entrega el sábado, devolución del ahorro). |
| EC-04 | Mi cuenta muestra arriba el saldo, lo devuelto y **lo ahorrado frente al supermercado** en todos los pedidos liquidados. Cada pedido es una tarjeta con su estado en palabras (S-146), sus productos y su avance. Los pedidos cancelables tienen botones "Cancelar y devolver a mi Yape/Plin" y "Cancelar y pasar a mi saldo" (S-147). Pedir devolución y cambiar PIN quedan en "Más opciones". |
| EC-05 | El panel del admin muestra el resumen de la semana (pedidos, pagos por verificar, dinero verificado, vecinos con pedido), los pagos por verificar con su botón, y la liquidación con una lista de los ciclos que tienen pedidos. |
| EC-08 | `POST /pedidos` desde la web genera el código de pago (S-150) y calcula el monto (S-148). La confirmación muestra "Yapea S/ X" y el código, destacados. Si el saldo cubre todo, dice que no hay que yapear. Si llegan `codigo` y `monto` (API), se usan como antes. |
| EC-09 | Las fotos se suben como archivo (S-151) y la ubicación de la zona se llena con un botón (S-152). |
| EC-07 | Se elige de una lista (S-149): el ciclo en Métricas, Catálogo y Liquidar; el pedido en Colchón; el vecino al reiniciar el PIN; la zona al unirse, al pedir la unión y el nuevo admin al transferir. El catálogo agrupa los productos por categoría en secciones desplegables. |
| EC-06 | Las acciones que salen bien se muestran como éxito (✓, en verde); los errores muestran el mensaje, el código y un enlace para volver. Las páginas de error (404, 405, 403) no se muestran como éxito. |

## Criterios de aceptación

Hora fija: miércoles 16/09/2026 a las 10:00 (2026-W38), catálogo base del piloto, Ana Torres (101) con sesión.

- **EC-A · Botones del catálogo.** Con sesión, cada producto tiene botones − y + (`data-step` con el paso del producto: 0.25 en el ajo) y la barra "Tu carrito" con el mínimo de S/ 50.00. Sin sesión no hay barra. → EC-01
- **EC-B · Tu carrito.** `POST /cotizar` con 5 kg de papa amarilla, 10 de papa blanca y 10 de cebolla roja muestra "Tu carrito", los nombres "Papa amarilla", "Papa blanca" y "Cebolla roja", "Total a yapear: S/ 61.00", y un formulario hacia `/pedidos` con `cant_PAPA-AMARILLA` = 5. → EC-02
- **EC-C · Ahorro en el carrito.** Con precio de supermercado de S/ 7.99 para la papa amarilla, el carrito dice "frente al supermercado" con el ahorro aprox. de esa línea: 5 × 7.99 − S/ 20.16 = **S/ 19.79**. → EC-02, S-145
- **EC-D · Saldo con una casilla.** Si Ana tiene S/ 10.00 de saldo, el carrito tiene la casilla `usar_saldo` con "Usar mi saldo (S/ 10.00)" y no tiene campos `codigo` ni `monto`. Al registrar con la casilla marcada, el pedido usa S/ 10.00 de saldo y la confirmación dice "Yapea S/ 51.00". → S-148, EC-08
- **EC-E · Confirmación.** Al registrar se ve "Ana", "Pedido 1", "Registrado" y "sábado". → EC-03
- **EC-F · Cancelar con botón.** Con un pedido registrado, Mi cuenta tiene un formulario a `/cuenta/cancelar` con `name="pedido" value="1"` y los botones con `destino` `MEDIO_DE_PAGO` y `SALDO`, y **no** tiene un campo para escribir el número de pedido. Tras cancelar a saldo, el pedido dice "Cancelado" y ya no tiene botones. → EC-04, S-147
- **EC-G · Ahorro acumulado.** En la semana de demo (30/09/2026), Mi cuenta de Ana muestra "Ahorraste S/ 42.31 frente al supermercado". → EC-04
- **EC-H · Panel del admin.** Con un pedido por verificar de S/ 61.00, el panel muestra el resumen ("Pedidos de la semana" 1, "Por verificar" 1) y la liquidación como lista con la opción `2026-W38`. → EC-05
- **EC-I · Mensajes.** Verificar un pago muestra la página de éxito (`class="card ok"`). Una ruta inexistente responde 404 sin `class="card ok"`. Un error de negocio muestra el código y un enlace "Volver". → EC-06

- **EC-J · Listas en vez de escribir.** `/admin/metricas` tiene `<select name="ciclo">`; `/admin/colchon`, `<select name="pedido">`; `/admin/vecinos`, `<select name="cliente">`; `/zona`, `<select name="zona">` para unirse. El catálogo con sesión tiene `<details` por categoría. → EC-07, S-149

- **EC-K · Código de pago generado.** Al registrar desde el carrito (solo medio YAPE, sin código ni monto), el pedido 1 queda con un código `YP-2026W38-101-XXXX`, la confirmación lo muestra junto a "Yapea S/ 61.00", y el admin lo ve en los pagos por verificar. → EC-08, S-150
- **EC-L · Foto como archivo.** El formulario de reclamo es `multipart/form-data` con `<input type="file" name="foto_archivo"`. Un reclamo enviado con un archivo `cebolla.jpg` guarda una foto `fotos/…jpg` cuyo contenido es el archivo enviado. → EC-09, S-151
- **EC-M · Ubicación con botón.** El formulario de crear zona tiene el botón "Usar mi ubicación". → EC-09, S-152

## Cambios en criterios anteriores (por S-146)

- **WA-05:** la confirmación dice "Registrado" (antes "REGISTRADO").
- **WA-08:** Mi cuenta dice "Cancelado" (antes "CANCELADO_POR_CLIENTE").

El resto de los criterios no cambia.

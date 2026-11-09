# Yapa — CUS-P01 Registrar pedido semanal

**Versión:** 2 (reglas oficiales C-01..C-12 y S-01..S-12; código de pago S-150). Reemplaza la versión basada en el Entregable 1 (delivery de S/ 7,90, ventana elegida por el cliente y contraentrega).
**Fuente de las reglas:** `api/docs/sdd/10-clarificaciones-v2.md`, `02-especificacion-cun-02.md` y `docs/desarrollo/04-cancelar-editar.md` y `26-experiencia-compra.md`.

## 0. Objetivo y frontera

Permitir que un vecino de una zona Yapa arme su canasta de la semana, vea el **precio máximo** que pagará y registre su pedido con un **código de pago** para yapear o plinear por adelantado.

La frontera es la aplicación web de Yapa. El vecino es el actor principal. Yape y Plin no son actores del sistema: no tienen API pública y el vecino paga fuera de la aplicación con el código que le da Yapa. La verificación de ese pago la hace el administrador y pertenece a CUN-03 (Procesar pago).

## 1. Requerimientos funcionales

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-P01 | El sistema debe mostrar los productos activos del catálogo del ciclo con su unidad, paso y **precio máximo** (precio del primer tramo del proveedor × (1 + comisión de la categoría)). | C-01, C-11, C-12, RP-06, RP-09 | Un producto inactivo o sin catálogo del ciclo no se puede pedir. El precio lo calcula el sistema; el vecino no lo envía. |
| RF-P02 | El sistema debe permitir elegir cantidades con botones − y + que respeten el paso del producto y el tope por línea. | S-08, RP-05, RP-07 | Una cantidad cero, que no sea múltiplo del paso o que supere 10 kg o 6 unidades se rechaza con `INVALID_QUANTITY`. Una canasta vacía se rechaza con `EMPTY_ORDER`. |
| RF-P03 | El sistema debe tomar la zona del registro del vecino y validar que esté activa y en un distrito piloto (Lince, Jesús María, La Victoria). | C-07, S-01, RP-02 | Si la zona no está activa, se rechaza con `ZONE_NOT_AVAILABLE`. El vecino no escribe una dirección. |
| RF-P04 | El sistema debe aceptar pedidos solo desde el lunes 00:00 hasta antes del miércoles 20:00, hora de Lima. | S-02, RP-03 | A las 20:00:00 exactas del miércoles se rechaza con `CYCLE_CLOSED`. |
| RF-P05 | El sistema debe permitir un solo pedido **activo** por vecino y ciclo. | S-03, RP-04, CE-06 | Un segundo pedido se rechaza con `ORDER_ALREADY_EXISTS`; si el primero se canceló, se permite otro. |
| RF-P06 | El sistema debe impedir vender más que la cantidad máxima declarada por el proveedor. | C-12, RP-08 | Si lo reservado más lo pedido supera el máximo, se rechaza con `PRODUCT_SOLD_OUT`. |
| RF-P07 | El sistema debe cotizar el carrito: subtotal exacto, envío con tope de S/ 5,00 y total redondeado al céntimo a favor del vecino. Debe exigir un subtotal mínimo de S/ 50,00. | S-04, S-05, S-09, C-09, RP-10, RP-11 | Con subtotal S/ 49,99 se rechaza con `SUBTOTAL_BELOW_MINIMUM` e informa que falta S/ 0,01. La cotización no reserva stock. |
| RF-P08 | El sistema debe permitir usar el saldo a favor hasta cubrir el total. El monto a yapear es el total menos el saldo usado; el vecino no lo escribe. | C-05, S-148 | Con S/ 10,00 de saldo y total S/ 61,00, se indica "Yapea S/ 51,00". Si el saldo cubre todo, se indica que no hay que yapear. |
| RF-P09 | El sistema debe aceptar solo Yape o Plin como medio de pago. | C-03, RP-12 | Otro medio se rechaza con `PAYMENT_METHOD_NOT_ALLOWED`. No existe contraentrega. |
| RF-P10 | Al registrar, el sistema debe reservar el stock, generar un código de pago único `YP-<semana>-<cliente>-<4 caracteres>` y crear el pedido en estado `REGISTRADO` con pago `POR_VERIFICAR`, todo como una sola operación. | C-04, S-150 | La confirmación muestra el número de pedido, el monto a yapear y el código. Si el registro falla, no queda stock reservado ni código usado. |

## 2. Requerimientos no funcionales

| ID | Requerimiento | Criterio de aceptación |
|---|---|---|
| RNF-P01 | Los importes intermedios se guardan exactos; solo el total se redondea, y siempre a favor del vecino (Ley 29571, art. 44). | 54,518 + 5,00 = 59,518 se cobra como S/ 59,51. |
| RNF-P02 | Solo un vecino con sesión iniciada registra pedidos a su nombre; cada POST lleva token CSRF. | Sin sesión se redirige a `/entrar`; un POST sin token se rechaza. |
| RNF-P03 | Cada error tiene un código estable (el contrato que se prueba) y un mensaje en español claro. | Ver la lista de la sección 5. |
| RNF-P04 | La web es responsiva y usable desde el celular (botones de al menos 44 px). | El flujo completo se puede hacer a 390 px de ancho. |

## 3. Ficha del caso de uso

| Campo | Descripción |
|---|---|
| Identificador | CUS-P01 |
| Nombre | Registrar pedido semanal |
| Actor principal | Vecino (cliente) |
| Actor secundario | — (el administrador verifica el pago en CUN-03) |
| Disparador | El vecino toca "Tu carrito" desde el catálogo de la semana. |
| Precondiciones | Vecino con sesión iniciada, no suspendido, inscrito en una zona; catálogo del ciclo publicado. |
| Postcondición de éxito | Pedido `REGISTRADO` con pago `POR_VERIFICAR`, líneas con su precio máximo, stock reservado y código de pago generado. Si usó saldo, el saldo queda descontado. |
| Garantía ante fallo | No se crea el pedido, no se reserva stock, no se descuenta saldo ni se usa un código. El vecino conserva su carrito. |
| Requisitos asociados | RF-P01 a RF-P10 y RNF-P01 a RNF-P04. |

## 4. Flujo principal

| Paso | Vecino | Sistema |
|---|---|---|
| 1 | Abre el catálogo de la semana. | Muestra los productos activos del ciclo por categoría, con precio máximo y, si existe, el precio de supermercado como referencia. |
| 2 | Agrega productos con − y +. | Actualiza la barra "Tu carrito" con artículos, total aproximado, cuánto falta para el mínimo y ahorro aproximado. |
| 3 | Toca "Tu carrito". | Cotiza en el servidor (RP-05..RP-11): muestra cada línea, subtotal, envío de S/ 5,00 y el total a yapear. |
| 4 | Marca "Usar mi saldo" si tiene saldo, y elige Yape o Plin. | Recalcula el monto a yapear (total − saldo usado). |
| 5 | Confirma el pedido. | Revalida en el orden fijo de S-11: vecino → zona → ciclo → pedido activo → líneas → stock → subtotal → pago. |
| 6 | — | Reserva el stock, descuenta el saldo usado, genera el código de pago y guarda el pedido como una sola operación. |
| 7 | Ve la confirmación. | Muestra el número de pedido, "Yapea S/ X" y el código `YP-…` destacados, con la indicación de ponerlo en el mensaje del Yape o Plin. |
| 8 | Paga desde su app de Yape o Plin, con el código en el mensaje. | — (fuera del sistema; el administrador lo verifica en CUN-03 antes del cierre). |

La ventana de entrega no la elige el vecino: Yapa la asigna a la zona y el pedido se recibe en la portería o con el encargado (S-10).

## 5. Flujos alternativos y excepciones

| Código | Punto | Condición | Respuesta |
|---|---|---|---|
| FA-01 | 3 o 5 | Canasta vacía (`EMPTY_ORDER`), producto inactivo (`PRODUCT_NOT_AVAILABLE`) o cantidad inválida (`INVALID_QUANTITY`). | Indica el producto y el problema, y vuelve al catálogo. |
| FA-02 | 5 | La zona del vecino no está activa (`ZONE_NOT_AVAILABLE`). | Informa que su zona todavía no recibe pedidos y lo lleva a la página de su zona. |
| FA-03 | 3 o 5 | Subtotal menor a S/ 50,00 (`SUBTOTAL_BELOW_MINIMUM`). | Muestra cuánto falta y permite seguir comprando. |
| FA-04 | 5 | El producto se agotó mientras armaba el carrito (`PRODUCT_SOLD_OUT`). | Indica el producto agotado y permite bajar la cantidad o quitarlo. |
| FA-05 | 5 | Ya tiene un pedido activo en el ciclo (`ORDER_ALREADY_EXISTS`). | Lo lleva a "Mis pedidos", donde puede editarlo o cancelarlo (CE). |
| FA-06 | 4 | El saldo cubre todo el total. | La confirmación dice que no hay que yapear; el pedido queda pagado con saldo. |
| EX-01 | 5 | El ciclo ya cerró (`CYCLE_CLOSED`). | Informa el cierre y la fecha de apertura del siguiente ciclo. |
| EX-02 | 5 | Vecino suspendido (`CUSTOMER_SUSPENDED`). | Informa la suspensión y el contacto de atención. |
| EX-03 | 6 | Falla el guardado. | La transacción se revierte entera (S-90..S-94); no se muestra éxito y el vecino puede reintentar. |

## 6. Reglas aplicadas

| Regla | Descripción | Reemplaza a |
|---|---|---|
| C-01 | Precio máximo garantizado: nunca se paga más de lo que se vio. | RN-21 (cobro del saldo en la entrega, eliminado por Ley 29571) |
| C-02 | Todos pagan el precio máximo y el ahorro se devuelve después (liquidación, fuera de este CUS). | RN-06 (variación de peso ±5 %) |
| C-03 | Solo pago anticipado con Yape o Plin. | RN-10 (transferencia, billetera y contraentrega) |
| C-04 / S-150 | Código de pago único, generado por Yapa. | RN-12 (referencia única) |
| C-07 / S-01 | La zona (punto de recepción) reemplaza a la dirección; distritos piloto. | RN-01, RN-07 |
| C-09 / S-05 | Envío compartido con tope de S/ 5,00. | RN-04 (delivery S/ 7,90, gratis desde S/ 120) |
| C-11 / S-08 | Frescos en pasos fijos de kg; tope de 10 kg o 6 unidades por línea. | RN-06 |
| C-12 | No se vende más que el máximo declarado por el proveedor. | — |
| S-02 | Recepción de lunes 00:00 a antes del miércoles 20:00. | RN-02 (el pedido tardío ya no pasa al siguiente ciclo) |
| S-04 | Mínimo de S/ 50,00 sobre el subtotal exacto. | RN-03 |
| S-10 | Yapa asigna la ventana a la zona. | RN-09 (ventana elegida por el cliente) |

## 7. Escenarios de aceptación

Salen de las especificaciones y las pruebas del motor (`api/tests/test_order_registration.py`, criterios EC-D y EC-K de la iteración 26).

1. **Pedido válido.** 5 kg de papa amarilla, 3 kg de cebolla roja, 2 kg de limón, 1 kg de ajo y 2 galones de limpiatodo: subtotal S/ 54,518, envío S/ 5,00, total **S/ 59,51**. Queda `REGISTRADO` / `POR_VERIFICAR` con código `YP-2026W38-101-XXXX`.
2. **Bajo el mínimo.** Subtotal S/ 49,99: se rechaza y se informa que falta S/ 0,01.
3. **Con saldo.** Saldo de S/ 10,00 y total S/ 61,00: la confirmación dice "Yapea S/ 51,00".
4. **Fuera de hora.** Miércoles a las 20:00:00: `CYCLE_CLOSED`.
5. **Segundo pedido.** Con un pedido activo, otro se rechaza; tras cancelarlo, se acepta.
6. **Agotado.** El proveedor declaró 400 kg de papa amarilla y ya hay 395 kg reservados: un pedido de 6 kg se rechaza con `PRODUCT_SOLD_OUT`; uno de 5 kg se acepta y deja la reserva en 400 kg (CA-10).
7. **Fallo al guardar.** No queda pedido parcial, stock reservado ni saldo descontado.

## 8. Documentos relacionados

- [Modelo de análisis](analisis-registrar-pedido.md).
- Especificación SDD: `api/docs/sdd/02-especificacion-cun-02.md`.
- Cancelar y editar: `api/docs/desarrollo/04-cancelar-editar.md`.
- [Modelado del negocio de origen](reference/Entregable01_ModeladoNegocio_Yapa.pdf).

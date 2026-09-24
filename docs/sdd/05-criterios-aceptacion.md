# Criterios de aceptación · iteración 2

Todos los escenarios usan el catálogo piloto de ejemplo (S-12), con comisión de 12 % en frescos y 9 % en limpieza, y el ciclo 2026-W38 (lunes 14/09 al miércoles 16/09 a las 20:00, hora de Lima).

## Registrar pedido (CUN-02)

**CA-01 · Pedido válido.**
DADO un cliente activo de una zona activa de Lince, dentro del ciclo, con 5 kg de papa amarilla, 3 kg de cebolla, 2 kg de limón, 1 kg de ajo y 2 galones de limpiatodo, que pagó S/ 59.51 por Yape con un código nuevo,
CUANDO registra el pedido,
ENTONCES el sistema lo crea `REGISTRADO` con pago `POR_VERIFICAR`, precio máximo de papa amarilla S/ 4.032, subtotal S/ 54.518, envío S/ 5.00 y total S/ 59.51. → RP-09, RP-10, RP-11

**CA-02 · Cliente suspendido.**
DADO un cliente suspendido,
CUANDO intenta registrar un pedido,
ENTONCES se rechaza con `CUSTOMER_SUSPENDED`. → RP-01

**CA-03 · Zona no disponible.**
DADO un cliente cuya zona está fuera de los distritos piloto, o cuya zona aún no tiene el punto de recepción aceptado,
CUANDO intenta registrar un pedido,
ENTONCES se rechaza con `ZONE_NOT_AVAILABLE`. → RP-02

**CA-04 · Límite del ciclo.**
DADO un pedido válido,
CUANDO se registra el miércoles a las 19:59:59, ENTONCES se acepta;
CUANDO se registra el miércoles a las 20:00:00, ENTONCES se rechaza con `CYCLE_CLOSED`;
CUANDO se registra el jueves, ENTONCES se rechaza con `CYCLE_CLOSED`. → RP-03

**CA-05 · Un pedido por ciclo.**
DADO un cliente que ya registró su pedido del ciclo,
CUANDO intenta registrar otro,
ENTONCES se rechaza con `ORDER_ALREADY_EXISTS`. → RP-04

**CA-06 · Pedido vacío.**
DADO un pedido sin líneas,
ENTONCES se rechaza con `EMPTY_ORDER`. → RP-05

**CA-07 · Líneas repetidas.**
DADO un pedido con papa amarilla en dos líneas de 3 kg,
ENTONCES se registra una sola línea de 6 kg. → RP-05

**CA-08 · Producto no disponible.**
DADO un producto que no está en el catálogo del ciclo o está inactivo,
ENTONCES se rechaza con `PRODUCT_NOT_AVAILABLE`. → RP-06

**CA-09 · Cantidad inválida.**
DADO 0.5 kg de papa (paso de 1 kg), 11 kg de papa (tope de 10 kg), 1.5 galones o 0 kg,
ENTONCES se rechaza con `INVALID_QUANTITY`. 0.25 kg de ajo (paso de 0.25 kg) sí se acepta. → RP-07

**CA-10 · Stock del proveedor.**
DADO que la papa amarilla tiene un máximo de 400 kg y ya hay 395 kg reservados,
CUANDO alguien pide 6 kg, ENTONCES se rechaza con `PRODUCT_SOLD_OUT`;
CUANDO pide 5 kg, ENTONCES se acepta. → RP-08

**CA-11 · Mínimo individual.**
DADO un subtotal exacto de S/ 49.99,
ENTONCES se rechaza con `SUBTOTAL_BELOW_MINIMUM` y el error informa que faltan S/ 0.01.
Un subtotal exacto de S/ 50.00 sí se acepta. → RP-10

**CA-12 · Pago.**
DADO un pedido válido:
- con medio `TARJETA` → `PAYMENT_METHOD_NOT_ALLOWED`;
- sin código de operación → `PAYMENT_CODE_REQUIRED`;
- con un código ya usado en otro pedido → `PAYMENT_CODE_ALREADY_USED`;
- con un monto distinto del total → `PAYMENT_AMOUNT_MISMATCH`.
→ RP-12, RP-13, RP-14

**CA-13 · Precio del sistema.**
DADO cualquier pedido,
ENTONCES el precio por unidad sale del catálogo (primer tramo × (1 + comisión)). El cliente no puede enviarlo. → RP-09

**CA-14 · Verificación del pago.**
DADO un pedido registrado,
CUANDO el administrador verifica el pago antes del cierre, ENTONCES el pago queda `VERIFICADO`;
CUANDO lo intenta después del cierre, ENTONCES se rechaza con `CYCLE_CLOSED`. → RP-15

## Liquidación del ciclo

**CL-01 · Pedidos sin pago verificado.**
DADO un pedido que sigue `POR_VERIFICAR` al cierre,
CUANDO se liquida,
ENTONCES queda `CANCELADO`, no cuenta para el mínimo ni para los tramos, y no tiene reembolso automático. → LQ-01

**CL-02 · Zona que no llega al mínimo.**
DADO un grupo de zonas con 7 pedidos verificados,
CUANDO se liquida,
ENTONCES esos 7 pedidos quedan `NO_ATENDIDO` y a cada uno se le devuelve el 100 % de lo pagado con destino `MEDIO_DE_PAGO`. → LQ-02

**CL-03 · Zonas unidas.**
DADO dos zonas del mismo grupo con 4 pedidos cada una,
CUANDO se liquida,
ENTONCES los 8 pedidos se atienden. → LQ-02

**CL-04 · Descuento por volumen.**
DADO que entre todos los pedidos atendidos se piden 100 kg de papa amarilla,
CUANDO se liquida,
ENTONCES el precio final es 3.38 × 1.12 = S/ 3.7856 por kg. → LQ-03, LQ-04

**CL-05 · Los que se retiran no hacen perder a Yapa.**
DADO que la papa amarilla habría llegado a 100 kg, pero un pedido quedó `CANCELADO` y el total atendido bajó a 95 kg,
CUANDO se liquida,
ENTONCES se aplica el primer tramo (S/ 4.032) y ningún cliente tiene saldo negativo. → LQ-04, LQ-08

**CL-06 · Envío compartido.**
DADO una zona con 10 pedidos atendidos y una parada de S/ 40,
ENTONCES el envío real es S/ 4.00 y a cada uno le vuelve S/ 1.00.
DADO una zona con 4 pedidos atendidos y una parada de S/ 40,
ENTONCES el envío real queda en el tope de S/ 5.00 (Yapa absorbe el resto). → LQ-05

**CL-07 · Artículo faltante.**
DADO un pedido con 2 kg de limón, de los que falta 1 kg,
ENTONCES solo se cobra 1 kg y el otro vuelve en el saldo.
Un faltante mayor que lo pedido, o de un producto que no está en el pedido, se rechaza con `INVALID_MISSING_ITEM`. → LQ-06

**CL-08 · Nunca se paga de más.**
DADO cualquier ciclo liquidado,
ENTONCES en cada pedido `LIQUIDADO` el saldo es ≥ 0 y monto final + saldo = monto pagado. → LQ-07, LQ-08

**CL-09 · Resumen transparente.**
DADO un ciclo liquidado,
ENTONCES el resumen muestra, por producto, la cantidad total, el tramo alcanzado y el precio final, además del total devuelto como saldo y el total reembolsado. → LQ-09

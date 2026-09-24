# Especificación SDD · CUN-02 Registrar pedido semanal (v2)

## Requisito

Como vecino de una zona Yapa, quiero registrar mi pedido de la semana y pagarlo por adelantado, sabiendo que **nunca pagaré más de lo que veo**, para recibirlo el sábado en el punto de recepción de mi zona.

## Entrada

```json
{
  "customerId": 101,
  "lines": [
    {"productId": "PAPA-AMARILLA", "quantity": "5"},
    {"productId": "CEBOLLA-ROJA", "quantity": "3"},
    {"productId": "LIMON", "quantity": "2"},
    {"productId": "AJO", "quantity": "1"},
    {"productId": "LIMPIATODO-GALON", "quantity": "2"}
  ],
  "payment": {"method": "YAPE", "operationCode": "04512873", "amount": "59.51"},
  "requestedAt": "2026-09-16T10:00:00-05:00"
}
```

El cliente **no envía** el precio, la zona ni la validación de su dirección: el sistema los obtiene del catálogo del ciclo y del registro del cliente.

## Reglas (en orden de validación, S-11)

| Regla | Comportamiento | Error |
|---|---|---|
| RP-01 | El cliente debe existir y no estar suspendido. | `CUSTOMER_NOT_FOUND`, `CUSTOMER_SUSPENDED` |
| RP-02 | La zona del cliente debe estar activa (punto de recepción aceptado) y ubicada en un distrito piloto. | `ZONE_NOT_AVAILABLE` |
| RP-03 | El ciclo recibe pedidos desde el lunes 00:00 hasta **antes** del miércoles 20:00, hora de Lima. | `CYCLE_CLOSED` |
| RP-04 | Un solo pedido por cliente por ciclo. | `ORDER_ALREADY_EXISTS` |
| RP-05 | El pedido tiene al menos una línea. Si un producto aparece en varias líneas, se suma. | `EMPTY_ORDER` |
| RP-06 | Cada producto existe en el catálogo del ciclo y está activo. | `PRODUCT_NOT_AVAILABLE` |
| RP-07 | Cada cantidad es mayor que cero, múltiplo del paso del producto y no supera el tope por línea (10 kg o 6 unidades). | `INVALID_QUANTITY` |
| RP-08 | Lo ya reservado más lo pedido no supera la cantidad máxima que declaró el proveedor. | `PRODUCT_SOLD_OUT` |
| RP-09 | Precio máximo por unidad = precio del primer tramo del proveedor × (1 + comisión de la categoría). Lo calcula el sistema. | — |
| RP-10 | El subtotal exacto (sin redondear) debe ser ≥ S/ 50.00. El error informa cuánto falta. | `SUBTOTAL_BELOW_MINIMUM` |
| RP-11 | El envío que se cobra es el tope, S/ 5.00. Total = subtotal + envío, redondeado al céntimo **hacia abajo** (a favor del cliente). | — |
| RP-12 | El medio de pago es `YAPE` o `PLIN`. | `PAYMENT_METHOD_NOT_ALLOWED` |
| RP-13 | El código de operación es obligatorio y no puede haberse usado en otro pedido. | `PAYMENT_CODE_REQUIRED`, `PAYMENT_CODE_ALREADY_USED` |
| RP-14 | El monto pagado es igual al total. | `PAYMENT_AMOUNT_MISMATCH` |

Si todo es válido:

1. Se reserva la cantidad pedida contra el stock máximo del proveedor.
2. Se marca el código de operación como usado.
3. Se crea el pedido en estado `REGISTRADO` con pago `POR_VERIFICAR`.

## Cotización

Antes de pagar, el cliente pide una **cotización** con sus líneas. Se aplican las mismas reglas de producto, cantidad, stock y cálculo (RP-05..RP-11), y el sistema devuelve el total exacto que debe yapear. La cotización no reserva stock ni crea el pedido.

## Verificación del pago (administrador)

| Regla | Comportamiento | Error |
|---|---|---|
| RP-15 | El administrador verifica el pago de un pedido existente **antes del cierre**. El pago pasa a `VERIFICADO`. | `ORDER_NOT_FOUND`, `CYCLE_CLOSED` |

## Salida válida

```json
{
  "orderId": 1,
  "cycle": "2026-W38",
  "status": "REGISTRADO",
  "paymentStatus": "POR_VERIFICAR",
  "lines": [
    {"productId": "PAPA-AMARILLA", "quantity": "5", "maxUnitPrice": "4.032", "maxLineTotal": "20.160"},
    {"productId": "CEBOLLA-ROJA", "quantity": "3", "maxUnitPrice": "2.352", "maxLineTotal": "7.056"},
    {"productId": "LIMON", "quantity": "2", "maxUnitPrice": "2.352", "maxLineTotal": "4.704"},
    {"productId": "AJO", "quantity": "1", "maxUnitPrice": "5.376", "maxLineTotal": "5.376"},
    {"productId": "LIMPIATODO-GALON", "quantity": "2", "maxUnitPrice": "8.611", "maxLineTotal": "17.222"}
  ],
  "subtotal": "54.518",
  "deliveryFee": "5.00",
  "total": "59.51"
}
```

Los importes intermedios se guardan exactos, sin redondear. El total, que es lo que se paga, va redondeado al céntimo a favor del cliente.

## Errores observables

`CUSTOMER_NOT_FOUND`, `CUSTOMER_SUSPENDED`, `ZONE_NOT_AVAILABLE`, `CYCLE_CLOSED`, `ORDER_ALREADY_EXISTS`, `EMPTY_ORDER`, `PRODUCT_NOT_AVAILABLE`, `INVALID_QUANTITY`, `PRODUCT_SOLD_OUT`, `SUBTOTAL_BELOW_MINIMUM`, `PAYMENT_METHOD_NOT_ALLOWED`, `PAYMENT_CODE_REQUIRED`, `PAYMENT_CODE_ALREADY_USED`, `PAYMENT_AMOUNT_MISMATCH`, `ORDER_NOT_FOUND`.

Cada error tiene un **código** (el contrato que se prueba) y un mensaje en español para el cliente.

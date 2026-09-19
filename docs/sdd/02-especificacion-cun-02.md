# Especificación SDD · CUN-02 Registrar pedido semanal

## Requisito

Como cliente de una zona atendida, quiero registrar una canasta durante el ciclo semanal para reservar una entrega del sábado con un total claro y un medio de pago elegido.

## Entrada

```json
{
  "customerId": 100,
  "district": "Lince",
  "addressValidated": true,
  "lines": [
    {"productId": 10, "name": "Arroz", "quantity": 2, "unitPrice": "30.00", "unit": "kg"}
  ],
  "deliveryWindow": "SAT_09_12",
  "paymentMethod": "TRANSFERENCIA"
}
```

## Reglas y comportamiento

1. La dirección debe pertenecer a una zona piloto y estar validada.
2. La fecha actual debe estar dentro del ciclo: lunes 00:00 hasta miércoles 20:00.
3. El pedido debe tener al menos un producto activo y una cantidad mayor que cero.
4. Cada precio debe tener unidad y estar vigente en el momento del pedido.
5. El subtotal debe ser igual o mayor a S/ 50.
6. La tarifa es S/ 7.90 cuando el subtotal es menor a S/ 120; desde S/ 120 es S/ 0.
7. La ventana debe ser una de las tres ventanas del sábado y tener capacidad disponible.
8. El medio de pago debe ser transferencia, billetera digital o contraentrega.

## Salida válida

```json
{
  "orderId": 1200,
  "status": "REGISTRADO",
  "subtotal": "60.00",
  "deliveryFee": "7.90",
  "total": "67.90",
  "deliveryWindow": "SAT_09_12",
  "paymentMethod": "TRANSFERENCIA"
}
```

## Errores observables

- `ADDRESS_OUTSIDE_COVERAGE`
- `CYCLE_CLOSED`
- `SUBTOTAL_BELOW_MINIMUM`
- `PRODUCT_NOT_ACTIVE`
- `PRICE_NOT_VALID`
- `DELIVERY_WINDOW_FULL`
- `PAYMENT_METHOD_NOT_ALLOWED`


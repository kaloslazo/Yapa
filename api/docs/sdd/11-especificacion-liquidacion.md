# Especificación SDD · Liquidación del ciclo ("te devolvemos")

## Requisito

Como vecino que pagó el precio máximo, quiero que después de la entrega **me devuelvan lo que ahorramos entre todos** (descuentos por volumen, envío compartido y artículos que no llegaron), para pagar solo lo que realmente costó mi pedido.

Como Yapa, quiero que esa liquidación **nunca me haga perder** porque alguien se retiró, y que una zona que no llegó al mínimo no se atienda.

## Entrada

- Los pedidos del ciclo, con su estado de pago.
- Las zonas, cada una con su grupo (las zonas unidas comparten grupo) y el costo de su parada.
- El catálogo del ciclo con los tramos de precio por volumen.
- El reporte de entrega, con los artículos faltantes o dañados aprobados por pedido:

```json
{
  "missing": [
    {"orderId": 3, "productId": "LIMON", "quantity": "1"}
  ]
}
```

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| LQ-01 | Solo participan los pedidos con pago `VERIFICADO`. Los que siguen `POR_VERIFICAR` al cierre quedan `CANCELADO`: no se compran ni se liquidan. | — |
| LQ-02 | **Mínimo por grupo de zonas**: si los pedidos verificados de todas las zonas del grupo suman menos de 8, esos pedidos quedan `NO_ATENDIDO` y se les devuelve **el 100 % de lo pagado al medio de pago** (C-06). Una zona sin grupo es su propio grupo. | — |
| LQ-03 | La cantidad total de cada producto es la suma de lo **pedido** en los pedidos atendidos. El tramo se decide sobre lo pedido, porque el proveedor aliado se compromete a respetarlo (C-12). | — |
| LQ-04 | Precio final por unidad = precio del **mayor tramo alcanzado** × (1 + comisión). Nunca puede superar el precio máximo que se cobró. | — |
| LQ-05 | Envío real por pedido = costo de la parada de la zona ÷ pedidos atendidos de esa zona, con tope de S/ 5.00. | — |
| LQ-06 | La cantidad faltante de un artículo no se cobra. Debe ser mayor que cero, no puede superar lo pedido, no puede referirse a un producto que no está en el pedido y solo aplica a pedidos que se entregaron (atendidos). | `INVALID_MISSING_ITEM` |
| LQ-07 | Monto final = Σ (precio final × cantidad entregada) + envío real, redondeado al céntimo **hacia abajo**. | — |
| LQ-08 | Saldo a favor = monto pagado − monto final. **Nunca es negativo.** Se abona como `SALDO` y el pedido queda `LIQUIDADO`. | — |
| LQ-09 | El resumen del ciclo muestra el tramo alcanzado y el precio final de cada producto (transparencia), el total devuelto como saldo y el total reembolsado. | — |

## Salida (por pedido)

```json
{
  "orderId": 3,
  "status": "LIQUIDADO",
  "paid": "59.51",
  "lines": [
    {"productId": "LIMON", "ordered": "2", "missing": "1", "delivered": "1", "finalUnitPrice": "2.128"}
  ],
  "deliveryFee": "2.50",
  "finalAmount": "...",
  "refund": {"amount": "...", "destination": "SALDO"}
}
```

`NO_ATENDIDO` → `refund.destination = "MEDIO_DE_PAGO"` y `refund.amount = paid`.
`CANCELADO` → sin reembolso automático. Si el cliente sí pagó, atención al cliente revisa el caso (fuera de alcance).

## Propiedades que siempre se cumplen

1. Ningún cliente paga más de lo que vio al registrar (saldo ≥ 0).
2. Que un pedido se retire solo puede **reducir** el ahorro de los demás; nunca genera un cobro extra.
3. En los pedidos atendidos, el monto pagado es igual al monto final más el saldo devuelto.

# Criterios de aceptación

## CA-01 · Pedido válido

**DADO** un cliente con dirección validada en Lince, un ciclo abierto, un producto activo vigente, subtotal de S/ 50 o más, ventana disponible y medio permitido

**CUANDO** registra el pedido

**ENTONCES** el sistema devuelve un pedido `REGISTRADO` con subtotal, delivery, total, ventana y medio de pago.

## CA-02 · Zona fuera de cobertura

**DADO** un cliente cuya dirección está fuera de Lince, Jesús María o La Victoria

**CUANDO** intenta registrar el pedido

**ENTONCES** el sistema rechaza la operación con `ADDRESS_OUTSIDE_COVERAGE`.

## CA-03 · Subtotal mínimo

**DADO** un pedido con subtotal menor a S/ 50

**CUANDO** se intenta confirmar

**ENTONCES** el sistema rechaza la operación con `SUBTOTAL_BELOW_MINIMUM`.

## CA-04 · Tarifa de entrega

**DADO** un subtotal menor a S/ 120

**CUANDO** el pedido es válido

**ENTONCES** la tarifa es S/ 7.90.

**DADO** un subtotal de S/ 120 o más

**CUANDO** el pedido es válido

**ENTONCES** la tarifa es S/ 0.

## CA-05 · Ventana sin capacidad

**DADO** una ventana del sábado cuya reserva alcanzó la capacidad

**CUANDO** se intenta registrar el pedido

**ENTONCES** el sistema rechaza la operación con `DELIVERY_WINDOW_FULL`.

## CA-06 · Precio no vigente

**DADO** un producto cuyo precio no tiene unidad o no está vigente

**CUANDO** se intenta registrar el pedido

**ENTONCES** el sistema rechaza la operación con `PRICE_NOT_VALID`.


# Plan técnico

## Decisión

Implementar primero una función de dominio pura en Python 3.11, sin framework web ni persistencia. La entrega demuestra las reglas sin introducir infraestructura que no forma parte de la pregunta SDD.

## Modelo mínimo

- `CatalogItem`: producto, unidad, precio referencial, vigencia y estado.
- `CustomerAddress`: distrito y validación.
- `DeliveryWindow`: código, capacidad y reservas.
- `OrderLine`: producto y cantidad.
- `RegisteredOrder`: salida con importes y estado.

## Flujo

1. Validar zona y dirección.
2. Validar ciclo.
3. Validar líneas y vigencia de precios.
4. Calcular subtotal y delivery.
5. Validar ventana y medio de pago.
6. Construir pedido `REGISTRADO`.

## No decisión todavía

No se decide base de datos, proveedor de pagos, framework HTTP, autenticación ni servicio de mapas. Son decisiones de los módulos posteriores.


# Alcance SDD de esta entrega

## Incluido

### CUN-02 · Registrar pedido semanal

Validar y registrar un pedido durante el ciclo activo, con productos cotizados, dirección cubierta, subtotal, tarifa, ventana y medio de pago.

### Límite de CUN-03 · Procesar pago

El pedido conserva el medio elegido: `TRANSFERENCIA`, `BILLETERA_DIGITAL` o `CONTRAENTREGA`. La conciliación externa y la verificación de referencias quedan para el módulo completo de CUN-03.

## Reglas implementadas

- RN-01: solo Lince, Jesús María y La Victoria.
- RN-02: recepción desde lunes 00:00 hasta miércoles 20:00.
- RN-03: subtotal mínimo S/ 50.
- RN-04: delivery S/ 7.90 y gratis desde S/ 120.
- RN-05: unidad y vigencia de precio.
- RN-07: producto activo, dirección válida y ventana disponible.
- RN-09: ventanas del sábado con capacidad por zona.
- RN-10: medios de pago habilitados.

## Diferido

RN-06 y RN-21 requieren peso real y liquidación posterior. RN-08 requiere sustituciones o devoluciones. RN-11 y RN-12 requieren conciliación. RN-13 a RN-22 pertenecen a consolidación, abastecimiento, preparación, entrega e incidencias. Se documentan en el repositorio general y no se simulan aquí.

## Fuera de alcance

Catálogo administrativo, compra al mayorista, almacén, preparación física, mapas, rutas, reparto, pagos externos, notificaciones, incidencias, autenticación, persistencia y despliegue web.


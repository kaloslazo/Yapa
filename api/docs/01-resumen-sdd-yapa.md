# SDD aplicado a Yapa

> **Documento de la iteración 1 (19/09/2026).** La versión vigente del alcance, las reglas y la evidencia está en `README.md`, `docs/sdd/10-clarificaciones-v2.md` y `docs/verification-report.md`.

## Idea principal

Yapa es una plataforma web para consolidar compras mayoristas por zona. El cliente arma su pedido durante la semana, el negocio cierra el ciclo el miércoles a las 20:00, compra al por mayor y entrega el sábado.

Para esta entrega no se implementa todo Yapa. Se selecciona una vertical con reglas suficientes para demostrar SDD:

**Registrar pedido semanal**, con el contrato mínimo de pago que el pedido necesita.

## Qué exige SDD en este caso

La especificación debe hacer explícito lo que el documento de negocio ya sugiere:

- solo se atienden Lince, Jesús María y La Victoria;
- el ciclo recibe pedidos desde el lunes a las 00:00 hasta el miércoles a las 20:00;
- el subtotal mínimo es S/ 50;
- la tarifa es S/ 7.90 y se exonera desde S/ 120;
- cada precio debe tener unidad y vigencia;
- debe existir al menos un producto activo, una dirección válida y una ventana con capacidad;
- el cliente puede elegir transferencia, billetera digital o contraentrega.

Estas reglas se convierten en criterios de aceptación y luego en validaciones del código.

## Cadena de trazabilidad

```text
CUN-02 Registrar pedido semanal
        ↓
RN-01, RN-02, RN-03, RN-04, RN-05, RN-07, RN-09, RN-10
        ↓
criterios de aceptación
        ↓
plan y tareas
        ↓
order_registration.py
        ↓
tests/test_order_registration.py
```

## Qué queda fuera

No se simula una falsa completitud del proyecto. Consolidar pedidos, comprar, preparar, planificar rutas, entregar, cobrar saldos por peso e investigar incidencias son siguientes módulos. El repositorio general de Yapa los documenta como roadmap.

## Resultado

SDD funcionó para convertir una funcionalidad real del proyecto en un alcance pequeño, verificable y defendible. El valor está en que cada línea importante del ejemplo responde a una regla del negocio. La evidencia no permite afirmar que la aplicación completa esté construida ni que el diseño sea listo para operación comercial.


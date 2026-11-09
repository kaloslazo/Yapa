# Casos de uso del sistema y trazabilidad

Un CUS por cada caso de uso del negocio (CUN-01 a CUN-08). Las reglas y los criterios completos están en las specs de `api/docs/`; cada CUS cita su código (por ejemplo, `CT-03`), así que se puede seguir cualquier regla hasta su prueba. Ver también el [modelo de datos y la arquitectura](../modelo-datos-arquitectura.md).

## Trazabilidad CUN → CUS → spec → pruebas

| CUN | CUS | Specs (`api/docs/`) | Pruebas (`api/tests/`) | Estado |
|---|---|---|---|---|
| CUN-01 Catálogo y precios | [CUS-01](cus-01-catalogo-precios.md) | `desarrollo/06`, `20`, `22`, `54` (PV) | `test_catalog`, `test_web_catalog`, `test_reference`, `test_proveedores_transportistas` | Completo |
| CUN-02 Registrar pedido | [CUS-02](cus-02-registrar-pedido.md) · [análisis](analisis-02-registrar-pedido.md) | `sdd/02`, `desarrollo/04`, `26` | `test_order_registration`, `test_order_changes`, `test_web_experiencia` | Completo |
| CUN-03 Pago y saldo | [CUS-03](cus-03-procesar-pago.md) | `sdd/02` (RP-15), `desarrollo/03`, `19` | `test_wallet`, `test_audit`, `test_e2e_week` | Completo |
| CUN-04 Consolidar y liquidar | [CUS-04](cus-04-consolidar-zona.md) | `sdd/11`, `desarrollo/05`, `16`, `37`, `38` | `test_zones`, `test_settlement`, `test_failed_delivery`, `test_analisis` | Completo |
| CUN-05 Compra al proveedor | [CUS-05](cus-05-compra-proveedor.md) | `desarrollo/07` (CO), `21`, `54` (PV-06), `55` (CP) | `test_fulfillment` (CO), `test_gaps_packing`, `test_personal_por_rol` | Parcial: falta la compra real con faltantes (iteración 56) |
| CUN-06 Preparar pedidos | [CUS-06](cus-06-preparar-pedidos.md) | `desarrollo/07` (AR), `21`, `55` (AM) | `test_fulfillment` (AR), `test_gaps_packing`, `test_personal_por_rol` | Parcial: falta rotulado y dañados al armar (iteración 56) |
| CUN-07 Entrega | [CUS-07](cus-07-entrega.md) | `desarrollo/07` (EN), `16`, `54` (TR), `55` (PO) | `test_fulfillment` (EN), `test_failed_delivery`, `test_proveedores_transportistas`, `test_personal_por_rol` | Parcial: sin rutas; falta bloqueo del despacho (iteración 56) |
| CUN-08 Incidencias | [CUS-08](cus-08-incidencias.md) | `desarrollo/07` (RC, RV), `33`, `55` (AT) | `test_fulfillment` (RC, RV), `test_personal_por_rol` | Parcial: faltan incidencias de atención (iteración 56) |

Transversales (no son un CUN, pero sostienen a todos): acceso y cuentas (`desarrollo/10`, `24`, `40`, `41`, `45`, `46`), avisos (`42`, `43`), persistencia (`11`), seguridad (`30`, `50`, `51`, `53`) y despliegue (`44`, `52`).

## Lo que falta y quién decide

| Pendiente | Bloqueado por |
|---|---|
| Iteración 56: compra real con faltantes, rotulado, dañados al armar, bloqueo del despacho, incidencias de atención | Regla del equipo: cómo llegan los faltantes y dañados a la liquidación (toca el dinero) |
| Rutas de reparto (CUN-07) | Decidir si entran en el alcance o quedan fuera con justificación |
| Escenario de costos y % del ahorro que retiene Yapa | Decisión del equipo (`api/docs/desarrollo/supuestos-a-validar.md`) |
| Borrado de datos al retirar el consentimiento (Ley 29733) | Decisión del equipo |

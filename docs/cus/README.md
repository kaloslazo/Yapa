# Casos de uso del sistema y trazabilidad

Un CUS por cada caso de uso del negocio (CUN-01 a CUN-08). Las reglas y los criterios completos están en las specs de `api/docs/`; cada CUS cita su código (por ejemplo, `CT-03`), así que se puede seguir cualquier regla hasta su prueba. Ver también el [modelo de datos y la arquitectura](../modelo-datos-arquitectura.md).

## Trazabilidad CUN → CUS → spec → pruebas

| CUN | CUS | Specs (`api/docs/`) | Pruebas (`api/tests/`) | Estado |
|---|---|---|---|---|
| CUN-01 Catálogo y precios | [CUS-01](cus-01-catalogo-precios.md) | `desarrollo/06`, `20`, `22`, `54` (PV) | `test_catalog`, `test_web_catalog`, `test_reference`, `test_proveedores_transportistas` | Completo |
| CUN-02 Registrar pedido | [CUS-02](cus-02-registrar-pedido.md) · [análisis](analisis-02-registrar-pedido.md) | `sdd/02`, `desarrollo/04`, `26` | `test_order_registration`, `test_order_changes`, `test_web_experiencia` | Completo |
| CUN-03 Pago y saldo | [CUS-03](cus-03-procesar-pago.md) | `sdd/02` (RP-15), `desarrollo/03`, `19` | `test_wallet`, `test_audit`, `test_e2e_week` | Completo |
| CUN-04 Consolidar y liquidar | [CUS-04](cus-04-consolidar-zona.md) | `sdd/11`, `desarrollo/05`, `15`, `16`, `37`, `38`, `57` (AH) | `test_zones`, `test_settlement`, `test_failed_delivery`, `test_analisis`, `test_retiro_datos` | Completo |
| CUN-05 Compra al proveedor | [CUS-05](cus-05-compra-proveedor.md) | `desarrollo/07` (CO), `21`, `54` (PV-06), `55` (CP), `56` (CR) | `test_fulfillment` (CO), `test_gaps_packing`, `test_personal_por_rol`, `test_compra_real` | Completo |
| CUN-06 Preparar pedidos | [CUS-06](cus-06-preparar-pedidos.md) | `desarrollo/07` (AR), `21`, `55` (AM), `56` (DA, RT) | `test_fulfillment` (AR), `test_gaps_packing`, `test_personal_por_rol`, `test_compra_real` | Completo |
| CUN-07 Entrega | [CUS-07](cus-07-entrega.md) | `desarrollo/07` (EN), `16`, `54` (TR), `55` (PO), `56` (BD), `58` (SR, SG) | `test_fulfillment` (EN), `test_failed_delivery`, `test_proveedores_transportistas`, `test_personal_por_rol`, `test_compra_real`, `test_logistica` | Completo (rutas fuera del alcance) |
| CUN-08 Incidencias | [CUS-08](cus-08-incidencias.md) | `desarrollo/07` (RC, RV), `33`, `55` (AT), `56` (IN) | `test_fulfillment` (RC, RV), `test_personal_por_rol`, `test_compra_real` | Completo |

Transversales (no son un CUN, pero sostienen a todos): acceso y cuentas (`desarrollo/10`, `24`, `40`, `41`, `45`, `46`), retiro del consentimiento (`57`, RD), avisos (`42`, `43`), persistencia (`11`), seguridad (`30`, `50`, `51`, `53`) y despliegue (`44`, `52`).

## Decisiones cerradas el 09/11/2026

| Tema | Decisión | Dónde |
|---|---|---|
| Faltante del proveedor y dañado al armar | Colchón primero; el resto se descuenta desde el último pedido y vuelve como saldo | iteración 56 (S-296, S-297) |
| Rutas de reparto | Fuera del alcance del piloto; el orden de paradas se arma a mano | CUS-07 |
| Parte del ahorro que retiene Yapa | 25 % | iteración 57 (S-301) |
| Retiro del consentimiento (Ley 29733) | Se anonimiza y se conserva el dinero sin datos personales | iteración 57 (S-303, S-304) |
| Cobro | Plin negocios, sin comisión; el vecino puede pagar desde Yape | iteración 58 (S-305) |
| Flete y reparto | Los contrata y paga Yapa; el vecino sigue su pedido en 7 pasos | iteración 58 (S-306..S-309) |
| Escenario de costos | El real: Plin al 0 % y flete propio. Equilibrio con 24 pedidos por semana (flete de S/ 120) | iteración 58 (S-307) |

## Lo que sigue abierto

| Pendiente | Quién decide |
|---|---|
| Cotizar y contratar la empresa de flete (el monto real reemplaza los S/ 180 estimados) | Equipo |
| Abrir la cuenta Plin negocios y configurar `YAPA_PLIN_NUMERO` y `YAPA_PLIN_TITULAR` | Equipo |
| "Ver la app como un vecino" desde atención | Equipo (privacidad) |
| Precios del mercado de barrio (trabajo de campo) | Equipo (`api/docs/desarrollo/kit-validacion-campo.md`) |

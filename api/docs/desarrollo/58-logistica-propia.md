# Iteración 58 · Logística propia: cobro por Plin, flete de compra, salida a reparto y seguimiento del pedido

## Requisito

Como Yapa, quiero cobrar sin comisión y encargarme yo del flete y del reparto, porque el proveedor normalmente no entrega. Así le puedo mostrar al vecino en qué va su pedido en cada paso, y las métricas muestran el margen con los costos reales.

## Por qué

Kalos lo decidió el 09/11/2026, después de revisar las fuentes:

- **Cobro por Plin negocios (0 %).** Interbank no cobra comisión por recibir pagos con Plin (tope de S/ 500 por operación, y un pedido ronda los S/ 61). Desde abril de 2023, Yape y Plin funcionan entre sí (BCRP), así que el vecino también puede pagar desde Yape. Yape Empresa (2,95 %) es voluntario y está pensado para más de 5 UIT al mes (S/ 27 500 en 2026).
- **Yapa contrata y paga el flete.** El Gran Mercado Mayorista no tiene servicio de reparto. Makro entrega desde S/ 150, pero no a Lince ni a Jesús María. Un flete en camioneta en Lima cuesta entre S/ 120 y S/ 320 por servicio.
- **Yapa maneja toda la logística** para darle al vecino el estado de su pedido.

Con el simulador (25 % retenido, parada de S/ 40, comisión de frescos 12 %), el margen real llega a 0 con **24 pedidos por semana si el flete cuesta S/ 120, 35 si cuesta S/ 180 y 60 si cuesta S/ 320**. Por debajo de eso, Yapa pierde plata por el viaje de compra.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-305 | Yapa cobra en una cuenta **Plin negocios**. La confirmación del pedido dice a qué número pagar y a nombre de quién, y que también se puede pagar desde Yape. El número y el titular salen de `YAPA_PLIN_NUMERO` y `YAPA_PLIN_TITULAR`. **Como Yapa es un proyecto académico sin empresa constituida (Kalos, 09/11/2026), si no están configurados se usa una cuenta simulada, también en el servidor:** "999 000 111 · Yapa (cuenta simulada, proyecto UTEC)". | decisión del 09/11 |
| S-306 | **Flete de compra.** Compras (o el admin) registra el flete de la semana, después del cierre y una sola vez por ciclo: la empresa (1 a 80 caracteres) y el monto (mayor que 0, hasta S/ 2 000, con céntimos). | decisión del 09/11 |
| S-307 | **Margen real.** Se calcula con el cobro al 0 %, el armado a S/ 1,60, la atención a S/ 0,73 y el viaje de compra igual al flete registrado ÷ pedidos atendidos del ciclo. Si el flete no está registrado, se usan **S/ 180** (la cotización más baja encontrada el 09/11, entre S/ 180 y S/ 320) y se marca como estimado. Los escenarios optimista y pesimista siguen en el simulador. | S/ 180 estimado |
| S-308 | **Salida a reparto.** El transportista (o el admin) marca que salió hacia una zona. Requiere la compra registrada y todo armado, se hace una sola vez y antes de entregar o registrar la falla. Cada vecino recibe el aviso "Tu pedido va en camino". Registrar la entrega **no exige** haber marcado la salida; en ese caso el seguimiento la da por hecha al entregar. | — |
| S-309 | **Seguimiento del pedido.** Los pasos son: Pedido, Pago verificado, Comprado, Armado, En camino, Entregado y Te devolvemos. Comprado = la compra real del ciclo está registrada. Armado = el pedido tiene al menos una bolsa. En camino = se marcó la salida de su zona, o ya se entregó. Entregado = la zona se entregó. Te devolvemos = el pedido está liquidado. | 7 pasos |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| PL-01 | Un pedido con monto por pagar trae `pagar_a` (número y titular) cuando está configurado (S-305). | — |
| FL-01 | Solo compras o el admin registran el flete. | `NOT_AUTHORIZED` |
| FL-02 | El ciclo ya cerró. | `CYCLE_STILL_OPEN` |
| FL-03 | Una sola vez por ciclo. | `FREIGHT_ALREADY_REGISTERED` |
| FL-04 | La empresa tiene de 1 a 80 caracteres; el monto es mayor que 0, hasta S/ 2 000 y con hasta 2 decimales. | `INVALID_FREIGHT`, `INVALID_AMOUNT` |
| MR-01 | El margen real usa los costos de S-307. | — |
| MR-02 | La página de métricas muestra el flete (y si es estimado), el flete por pedido, el margen real promedio y cuántos pedidos pierden. | — |
| SR-01 | Marcar la salida: transportista o admin; la zona existe, no está entregada ni fallida, no salió antes, tiene pedidos atendidos todos armados, y la compra está registrada. | `NOT_AUTHORIZED`, `ZONE_NOT_FOUND`, `ZONE_ALREADY_CLOSED`, `ZONE_ALREADY_DISPATCHED`, `NOTHING_TO_DELIVER`, `ORDERS_NOT_PACKED`, `PURCHASE_NOT_REGISTERED` |
| SR-02 | Al salir, cada vecino de la zona recibe el aviso `EN_CAMINO`. | — |
| SG-01 | Cada pedido trae su seguimiento según S-309. | — |

## Criterios de aceptación

Escenario base: el de la iteración 56. W38, Z-JM-01 (Residencial San Felipe) con 8 pedidos verificados; se opera el viernes 18/09 y se entrega el sábado 19/09.

- **FL-A · Registrar el flete.** Compras registra "Fletes Santa Anita" por S/ 120,00 → queda guardado con su empresa y su monto. Registrarlo otra vez → `FREIGHT_ALREADY_REGISTERED`. → FL-01..FL-03
- **FL-B · Datos.** Empresa vacía o de 81 caracteres → `INVALID_FREIGHT`. Monto 0, −5, 2000,01, "abc" o 10,005 → `INVALID_AMOUNT`. Antes del cierre → `CYCLE_STILL_OPEN`. El armador o un vecino → `NOT_AUTHORIZED`. → FL-01, FL-02, FL-04
- **MR-A · Margen real con flete registrado.** Con S/ 120 de flete y 8 pedidos atendidos, el viaje es **S/ 15,00 por pedido** y el margen real de cada pedido es su margen de contribución − 15,00 − 1,60 − 0,73, sin comisión de cobro. → MR-01, S-307
- **MR-B · Sin flete registrado.** Se estima S/ 180: **S/ 22,50 por pedido**, marcado como estimado. → S-307
- **MR-C · Métricas.** `GET /api/admin/metricas` trae `margen_real` con `flete` "120.00", `estimado` falso, `por_pedido` "15.00", el promedio y la cantidad de pedidos que pierden. → MR-02
- **SR-A · Salida a reparto.** Con la compra registrada y todo armado, el transportista marca la salida a Z-JM-01 → los 8 vecinos reciben "Tu pedido va en camino". Marcarla otra vez → `ZONE_ALREADY_DISPATCHED`. Después se entrega normal. → SR-01, SR-02
- **SR-B · Bloqueos.** Sin compra → `PURCHASE_NOT_REGISTERED`. Con un pedido sin bolsa → `ORDERS_NOT_PACKED`. Con la zona ya entregada → `ZONE_ALREADY_CLOSED`. Una zona que no existe → `ZONE_NOT_FOUND`. El armador → `NOT_AUTHORIZED`. → SR-01
- **SG-A · Seguimiento paso a paso.** Para el pedido 1: al registrarlo y verificarlo están hechos Pedido y Pago verificado. Al registrar la compra se suma Comprado; al armar, Armado; al salir, En camino; al entregar, Entregado; al liquidar, Te devolvemos. → SG-01
- **SG-B · Entrega sin marcar la salida.** Si se entrega sin marcar la salida, En camino y Entregado quedan hechos los dos. → S-308
- **PL-A · A dónde pagar.** Con la API configurada con el Plin "999 000 111" a nombre de "Yapa (cuenta simulada, proyecto UTEC)", el pedido recién registrado trae `pagar_a` con ese número y titular; si la API no recibe cuenta, no trae `pagar_a`. El servidor sin variables usa la cuenta simulada (también en modo servidor); con las variables, usa esas. → PL-01, S-305

## Cambios en pruebas anteriores

Ninguno: la salida a reparto es opcional para entregar, y el seguimiento y `pagar_a` son datos nuevos de la respuesta.

## Trazabilidad

| Regla | Código | Pruebas (`tests/test_logistica.py`) |
|---|---|---|
| PL-01, S-305 | `pagar_a` en `order_json` (solo con el pago por verificar); `produccion.payee` lee `YAPA_PLIN_NUMERO` y `YAPA_PLIN_TITULAR` | `test_pl_a_order_says_where_to_pay`, `test_pl_a_payee_from_environment` |
| FL-01..FL-04, S-306 | `logistics.register_freight`; `POST /api/compras/flete` | `test_fl_a_*`, `test_fl_b_*`, `test_mr_c_*` |
| MR-01, S-307 | `logistics.real_costs` (con `metrics.net_margins`) | `test_mr_a_*`, `test_mr_b_*` |
| MR-02 | `margen_real` en `GET /api/admin/metricas` | `test_mr_c_metrics_show_real_margin` |
| SR-01, SR-02, S-308 | `logistics.dispatch_zone`; `POST /api/reparto/salidas` y `/api/admin/salidas`; estado `en_camino` en el reparto | `test_sr_a_*`, `test_sr_b_*`, `test_mr_c_*` |
| SG-01, S-309 | `logistics.tracking`; `seguimiento` en cada pedido | `test_sg_a_*`, `test_sg_b_*`, `test_pl_a_*` |
| Web | Seguimiento de 7 pasos (`OrdersPage.tsx`), a qué Plin pagar (`CheckoutDialog.tsx`), "Salí hacia esta zona" (`PartnerPanel.tsx`), flete y margen real (`AdminPanel.tsx`) | `src/services/mappers.test.ts` |

En la semana de demostración (9 pedidos atendidos y S/ 120 de flete), el margen real es **−S/ 9,57 por pedido**: con un solo grupo no alcanza para pagar el flete, como predice el punto de equilibrio de 24 pedidos.

Evidencia: `docs/evidencia/desarrollo/58-logistica-rojo.txt`, `58-logistica-web-rojo.txt`, `58-logistica-verde.txt` y `58-logistica-web-verde.txt`.


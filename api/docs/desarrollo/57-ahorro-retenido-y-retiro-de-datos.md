# Iteración 57 · Yapa retiene el 25 % del ahorro y el vecino puede retirar su consentimiento

## Requisito

Como Yapa, quiero quedarme con una parte del ahorro por volumen para no perder plata en el peor escenario, y decírselo claro al vecino. Como vecino, quiero poder retirar mi consentimiento de datos y que borren lo que me identifica.

## Por qué

Eran dos decisiones urgentes pendientes (`supuestos-a-validar.md`, preguntas 49 y 67). Kalos las decidió el 09/11/2026:

- **Ahorro:** Yapa retiene el **25 %**. Según el simulador (iteración 15), con 25 % el peor escenario deja de perder (−S/ 0,06 por pedido, antes −S/ 2,52) y el vecino igual recupera S/ 10,39.
- **Retiro del consentimiento (Ley 29733):** se **anonimiza**. Se borra lo que identifica al vecino y se conservan sus pedidos y su dinero sin datos personales, por contabilidad. Si tiene saldo, primero se le devuelve.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-301 | La liquidación **operativa** (`close_cycle`, la que usan la web y la demo) retiene el 25 % del ahorro por volumen con la regla RA-01 de la iteración 15: precio final = tramo + 25 % × (máximo − tramo). `settle_cycle` sigue siendo el cálculo puro con 0 % por defecto, para que las pruebas y el simulador conserven sus números. | 25 % |
| S-302 | La web dice el reparto donde explica el precio: "Si entre todos pedimos más y el precio baja, el 75 % de esa baja vuelve a tu saldo; el 25 % sostiene la operación de Yapa." (Ley 29571, información clara). | — |
| S-303 | El vecino retira su consentimiento desde Mi cuenta y lo confirma escribiendo `RETIRAR`. No puede hacerlo si tiene un pedido sin liquidar, saldo o una devolución pendiente, un reclamo pendiente, o si es admin de una zona (primero transfiere el rol). | — |
| S-304 | Al retirar: el nombre pasa a "Vecino retirado"; se borran celular, correo, ubicación, cuenta de Google y la fecha de consentimiento; se apagan los avisos por correo; la cuenta queda suspendida; se borra su PIN y se cierran sus sesiones; se anulan sus invitaciones; y se borran sus avisos, sus pedidos de PIN y sus códigos de correo. Se guarda la fecha del retiro. **Se conservan** sus pedidos, pagos, movimientos de saldo, devoluciones y reclamos, identificados solo por su número. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AH-01 | `close_cycle` liquida con el 25 % retenido (S-301). | — |
| AH-02 | La conciliación sigue en 0: lo retenido se cuenta como retenido. | — |
| RD-01 | La confirmación es exactamente `RETIRAR`. | `CONFIRMATION_REQUIRED` |
| RD-02 | Sin pedidos `REGISTRADO` (sin liquidar). | `HAS_ACTIVE_ORDER` |
| RD-03 | Saldo 0 y sin devoluciones pendientes. | `BALANCE_PENDING` |
| RD-04 | Sin reclamos pendientes. | `CLAIM_PENDING` |
| RD-05 | No es admin de una zona. | `ZONE_ADMIN_MUST_TRANSFER` |
| RD-06 | Se anonimiza según S-304. Un vecino ya retirado no puede volver a retirarse ni entrar. | `CUSTOMER_NOT_FOUND` |

## Criterios de aceptación

- **AH-A · 25 % en la liquidación operativa.** W38, Z-JM-01 con los 8 pedidos del escenario de la iteración 7 (10 kg de cebolla cada uno: 80 kg, tramo desde 80 a S/ 1,80). Precio máximo S/ 2,352 (2,10 × 1,12) y del tramo S/ 2,016 (1,80 × 1,12). Con la compra registrada, todo armado y entregado, `close_cycle` da un precio final de 2,016 + 0,25 × (2,352 − 2,016) = **S/ 2,100**; `settle_cycle` sin parámetro sigue en S/ 2,016. → AH-01, S-301
- **AH-B · Semana completa.** En la semana de punta a punta por la web (AU-C), la conciliación da 0 después de cada paso y el vecino 801 termina con menos saldo que con 0 % (el ahorro baja en un 25 %). → AH-02
- **AH-C · La web lo dice.** La pregunta "¿Cuánto voy a pagar?" de la portada menciona el 75 % y el 25 %. → S-302
- **RD-A · Retirar.** Un vecino sin pedidos, con saldo 0, retira con `RETIRAR` → nombre "Vecino retirado", sin celular, correo, ubicación ni Google; suspendido; sin PIN; su sesión se cierra; su invitación ya no sirve; sus avisos y pedidos de PIN se borran. Sus pedidos liquidados y sus movimientos de saldo siguen. → RD-06, S-304
- **RD-B · Bloqueos.** Con un pedido registrado → `HAS_ACTIVE_ORDER`; con S/ 5 de saldo → `BALANCE_PENDING`; con una devolución pendiente → `BALANCE_PENDING`; con un reclamo pendiente → `CLAIM_PENDING`; siendo admin de zona → `ZONE_ADMIN_MUST_TRANSFER`; confirmando con `retirar` o vacío → `CONFIRMATION_REQUIRED`. → RD-01..RD-05
- **RD-C · Después.** Entrar con su correo o su celular falla como un usuario que no existe; retirar otra vez → `CUSTOMER_NOT_FOUND`. → RD-06
- **RD-D · API.** `POST /api/cuenta/retirar-consentimiento` con `{"confirmar": "RETIRAR"}` responde 200 y la siguiente llamada con la misma cookie responde 401. → RD-06

## Cambios en pruebas anteriores (por S-301)

`test_e2e_week` (AU-C) liquida con `close_cycle` por la web: el saldo esperado del vecino 801 baja por el 25 % retenido. Se recalcula en la prueba antes del código; la conciliación sigue exigiendo 0.

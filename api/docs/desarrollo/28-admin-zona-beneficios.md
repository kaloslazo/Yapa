# Iteración 28 · Admin de zona: beneficios, referidos y su panel

## Requisito

Como vecino que organiza su edificio (admin de zona), quiero tener un beneficio por hacerlo, ver cómo va mi zona en la semana, invitar vecinos con mi código y unir o transferir mi zona desde un panel propio.

Como Yapa, quiero que los vecinos traigan a otros vecinos con un premio chico y medido, sin repetir el error de Favo (pagar sueldos a líderes) ni regalar plata sin cálculo.

## Por qué

- Pedido de Carlos (17/10/2026): el admin de zona tiene **envío gratis** y un **descuento temporal**, y Yapa usa **referidos** como canal de marketing.
- El análisis de antecedentes (doc 07) ya proponía "incentivo chico, sin sueldo, por ejemplo envío gratis para él", y la lección L2 (doc 05) pide que **todo beneficio tenga su costo calculado**. Por eso cada beneficio de esta iteración tiene un tope y su costo queda a la vista en la conciliación.
- La zona como tal (crear, radio de 300 m, unir a 500 m, transferir) ya está en la iteración 5. Aquí se agrega lo que el admin de zona **ve y gana**.

## Costo de cada beneficio (para que el equipo decida)

Con la canasta de prueba de S/ 61.00 y una zona de 8 pedidos (parada de S/ 40, S/ 5 por pedido):

| Beneficio | A quién | Costo para Yapa | Frente al margen |
|---|---|---|---|
| Envío gratis | admin de zona, cada semana que su zona se atiende | S/ 5.00 por semana y zona | ~1 pedido de margen (S/ 5.64) por semana; se paga si la zona suma 1 pedido más |
| Descuento temporal 5 % | admin de zona, primeras 4 semanas de su zona | ~S/ 2.64 por semana, máximo ~S/ 10.56 en total | costo de arranque, una sola vez por zona |
| Referido | quien invita y quien llega, cuando el nuevo recibe su primer pedido | S/ 3.00 + S/ 3.00 = S/ 6.00 por vecino nuevo que compra | se recupera con ~1 pedido del nuevo vecino |

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-158 | **Envío gratis del admin de zona.** Al liquidar, el pedido del admin actual de la zona no paga su parte del envío. Los demás vecinos pagan lo mismo que antes: Yapa absorbe esa parte. | S/ 0 de envío |
| S-159 | **Descuento temporal del admin de zona.** 5 % sobre los productos de sus pedidos liquidados en las primeras 4 semanas desde que se creó la zona (la semana de creación cuenta como la 1). Las zonas del piloto que no tienen fecha de creación no lo dan. | 5 %, 4 semanas |
| S-160 | Los beneficios del admin se aplican **al liquidar**, como saldo a favor ("te devolvemos"), nunca como un cobro distinto al que vio al pedir (C-01). | — |
| S-161 | **Código de referido.** Cada vecino tiene un código fijo: su primer nombre en mayúsculas, sin tildes, y su número de cliente (Ana Torres, 101 → `ANA101`). | — |
| S-162 | Al dar de alta a un vecino, el admin de Yapa puede anotar el código de quien lo invitó. Un código que no existe se rechaza. | — |
| S-163 | **Premio por referido.** Cuando el **primer** pedido del vecino nuevo queda liquidado, el que invitó y el invitado reciben S/ 3.00 de saldo cada uno, una sola vez por invitado. Si el que invitó está suspendido, no recibe el premio. | S/ 3.00 + S/ 3.00 |
| S-164 | Los premios por referido son dinero que Yapa pone de su margen: en la conciliación se restan de lo retenido, así la diferencia sigue en 0 (AU-02). | — |
| S-165 | El admin de zona ve los **nombres** de los vecinos de su zona y si ya pidieron esta semana, pero no sus montos ni sus ubicaciones (Ley 29733). | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AZ-01 | Envío gratis del admin de zona al liquidar (S-158). | — |
| AZ-02 | Descuento temporal del admin de zona al liquidar (S-159). | — |
| AZ-03 | Cada pedido liquidado guarda su `beneficio` (lo que bajó por AZ-01 y AZ-02), y Mi cuenta lo muestra. | — |
| AZ-04 | Código de referido de cada vecino (S-161). | — |
| AZ-05 | Alta con código de referido (S-162). | `REFERRAL_NOT_FOUND` |
| AZ-06 | Premio por referido al liquidar el primer pedido del invitado (S-163). | — |
| AZ-07 | La conciliación resta los premios de lo retenido (S-164). | — |
| AZ-08 | `GET /api/mi-zona` da al admin de zona: el avance del grupo en la semana (pedidos verificados frente a 8), sus vecinos con "ya pidió" (S-165), las zonas que están a 500 m o menos con su distancia (para unir), sus beneficios y su código de referido. | — |

## Criterios de aceptación

Hora fija: miércoles 16/09/2026 a las 10:00 (2026-W38). Zona Z-JM-01 con 8 vecinos (801 a 808) que piden la canasta de S/ 61.00 y pagan con Yape. Sin beneficios, cada uno paga al final S/ 57.64 (S/ 52.64 de productos y S/ 5.00 de envío) y se le devuelven S/ 3.36.

- **AZ-A · Envío gratis.** El 801 es admin de Z-JM-01 (zona sin fecha de creación). Al liquidar, su pedido cuesta **S/ 52.64**, se le devuelven **S/ 8.36** y su `beneficio` es S/ 5.00. Los otros 7 siguen en S/ 57.64. → AZ-01, AZ-03
- **AZ-B · Descuento temporal.** Si Z-JM-01 se creó en 2026-W37, el pedido del 801 cuesta **S/ 50.00** (52.64 × 0.95 = 50.008, al céntimo a favor del vecino), se le devuelven **S/ 11.00** y su beneficio es S/ 7.64. Si se creó en 2026-W34 (la semana 2026-W38 es la quinta), solo tiene envío gratis: S/ 52.64. → AZ-02
- **AZ-C · Sin admin no hay beneficio.** Si la zona no tiene admin, los 8 pagan S/ 57.64. → AZ-01
- **AZ-D · Código de referido.** Ana Torres (101) tiene el código `ANA101`; José Núñez (n.º 120) tendría `JOSE120`. → AZ-04
- **AZ-E · Alta con referido.** El admin da de alta a Lucía con el código `ANA101` → Lucía queda referida por 101. Con el código `NOEXISTE9` → `REFERRAL_NOT_FOUND` y no se crea. → AZ-05
- **AZ-F · Premio.** Si el 808 fue referido por el 801, al liquidar la semana el 801 recibe S/ 3.00 más de saldo y el 808 también (kind `PREMIO_REFERIDO`). En una segunda semana liquidada del 808 no hay otro premio. → AZ-06
- **AZ-G · Conciliación.** Después de AZ-A con AZ-F, `money_balance` da diferencia **0**. → AZ-07
- **AZ-H · Panel del admin de zona.** Con 3 pedidos verificados en el grupo, `GET /api/mi-zona` del admin dice `avance` 3 de 8, lista a sus vecinos con `pidio` verdadero solo para los que tienen pedido en la semana, incluye las zonas a 500 m o menos con su distancia en metros, dice `envio_gratis` verdadero y da su `codigo_referido`. Un vecino que no es admin no recibe el bloque `administra`. → AZ-08

## Hueco encontrado al implementar

- `seed.pilot_store()` agregaba a cada repositorio **las mismas instancias** de `Zone` de `PILOT_ZONES`. Como `Zone` es mutable (`admin_id`, `group_id`, `created_cycle`), cambiar una zona en un repositorio la cambiaba en todos los que se crearan después. Regla nueva **AZ-09**: cada repositorio del piloto recibe **copias** de las zonas. Se detectó porque AZ-C y AZ-F fallaban solo cuando AZ-A corría antes.

## Trazabilidad

| Regla | Código | Prueba (`tests/test_zone_benefits.py`) |
|---|---|---|
| AZ-01, AZ-02, AZ-03, S-158..S-160 | `settlement.settle_cycle` (envío 0 y 5 % para el admin), `_in_discount_weeks`, `SettledOrder.benefit`, `Zone.created_cycle` (lo pone `zones.create_zone`) | `test_az_a_*`, `test_az_b_*`, `test_az_c_*` |
| AZ-04, S-161 | `customers.referral_code` | `test_az_d_*` |
| AZ-05, S-162 | `customers.find_by_referral`, `register_customer(referral=...)`, `Customer.referred_by` | `test_az_e_*` |
| AZ-06, S-163 | `settlement._reward_referral` (`PREMIO_REFERIDO`) | `test_az_f_*` |
| AZ-07, S-164 | `audit.money_balance` resta los premios de lo retenido | `test_az_g_*` |
| AZ-08, S-165 | `web/api.py` `zone_admin_panel`, `mi_zona`; `codigo_referido` en `GET /api/sesion` | `test_az_h_*` |
| AZ-09 | `seed.pilot_store` agrega copias de las zonas | `test_az09_*` |

La semana de demo ahora tiene a Ana (101) como admin de Los Álamos desde la 2026-W40 (envío gratis y 5 % hasta la 2026-W43) y a Diana Rojas (115), invitada por Ana, con su primer pedido en la W40.


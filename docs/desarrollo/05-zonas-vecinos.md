# Iteración 5 · Zonas de vecinos

## Requisito

Como vecino, quiero crear la zona de mi edificio o barrio, invitar a mis vecinos y unirme con la zona de al lado si estamos cerca, para llegar juntos al mínimo.

Como Yapa, quiero que cada zona tenga un punto de recepción confirmado y que nadie de lejos se cuele en una zona, para que el camión haga una parada corta y no pierda tiempo ni plata.

## Decisiones del equipo que se aplican

- **C-07:**
  - La zona es un punto de recepción (portería o encargado) creado por un vecino admin.
  - Tiene radio máximo.
  - Las zonas cercanas pueden unirse con el acuerdo de sus dos admins; cuentan juntas para el mínimo y cada una tiene su propia parada.
- **Carlos, 23/09:**
  - El admin no toca plata: cada vecino paga directo a Yapa.
  - El rol se puede transferir, para que la zona no muera.
  - "Si están muy lejos es pérdida para el conductor."
- **Propuesta del 23/09:** la zona no se activa sin la aceptación de la portería o del encargado.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-25 | Radio máximo entre la casa de un vecino y el punto de recepción de su zona. | 300 m (≈ 3 cuadras) |
| S-26 | Distancia máxima entre los puntos de dos zonas unidas. Se exige respecto de **todas** las zonas del grupo, para que un grupo no se estire en cadena. | 500 m |
| S-27 | La distancia se calcula en línea recta (fórmula de Haversine) con las coordenadas del punto y de la casa. La geocodificación de direcciones queda fuera de alcance. | — |
| S-28 | Una zona nace `PENDIENTE_RECEPCION` y pasa a `ACTIVA` cuando el admin registra quién recibe: `PORTERIA`, `ENCARGADO` o `ADMIN`, con un nombre de contacto. Solo las zonas activas reciben pedidos (RP-02). | — |
| S-29 | Una persona es admin de una sola zona, y el admin es también vecino de su zona. | — |
| S-30 | Un vecino con un pedido activo en el ciclo abierto no puede cambiarse de zona hasta después de la liquidación. | — |
| S-31 | Unir zonas o separarlas solo se puede mientras el ciclo está abierto. Al cierre, los grupos quedan fijos para la liquidación. | — |
| S-32 | El costo de parada de una zona nueva lo fija Yapa: S/ 40 en el piloto. | S/ 40 |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| ZN-01 | Crear zona: el creador debe ser cliente, no ser admin de otra zona y tener ubicación. El distrito debe estar en el piloto. La zona nace `PENDIENTE_RECEPCION`, el creador queda como admin y como vecino de la zona, y la zona forma su propio grupo. | `CUSTOMER_NOT_FOUND`, `ALREADY_ADMIN`, `LOCATION_REQUIRED`, `DISTRICT_NOT_IN_PILOT`, `HAS_ACTIVE_ORDER` (S-30 también aplica al creador) |
| ZN-02 | Activar zona: solo el admin, indicando el tipo de recepción válido y un nombre de contacto. | `NOT_ZONE_ADMIN`, `INVALID_RECEPTION` |
| ZN-03 | Unirse a una zona: la zona existe; el vecino tiene ubicación a ≤ 300 m del punto y no tiene pedido activo en el ciclo abierto. | `ZONE_NOT_FOUND`, `LOCATION_REQUIRED`, `OUTSIDE_ZONE_RADIUS`, `HAS_ACTIVE_ORDER` |
| ZN-04 | Pedir unión: el admin de la zona A la pide para unirse al grupo de la zona B. La zona A debe estar a ≤ 500 m de todas las zonas del grupo de B, en otro grupo, y con el ciclo abierto. | `NOT_ZONE_ADMIN`, `ZONES_TOO_FAR`, `SAME_GROUP`, `CYCLE_CLOSED` |
| ZN-05 | Aceptar unión: solo el admin de la zona B. Al aceptar, A pasa al grupo de B. | `MERGE_REQUEST_NOT_FOUND`, `NOT_ZONE_ADMIN`, `CYCLE_CLOSED` |
| ZN-06 | Salir del grupo: el admin de la zona la separa y vuelve a su propio grupo (con el ciclo abierto). | `NOT_ZONE_ADMIN`, `CYCLE_CLOSED` |
| ZN-07 | Transferir el rol de admin: solo el admin actual, y a un vecino de la misma zona que no sea admin de otra zona. | `NOT_ZONE_ADMIN`, `NOT_ZONE_MEMBER`, `ALREADY_ADMIN` |
| ZN-08 | El admin no maneja dinero: ninguna operación de zonas mueve pagos ni saldo. | — |

## Criterios de aceptación

Coordenadas de prueba alrededor de un punto de Lince (lat −12.0850, lon −77.0350). Cada 0.0009° de latitud son ≈ 100 m.

- **ZA-01 · Crear zona.** Un vecino de Lince crea "Edificio Los Pinos" → queda `PENDIENTE_RECEPCION`, es su admin y su vecino. Si intenta pedir, recibe `ZONE_NOT_AVAILABLE` (la zona aún no está activa). → ZN-01, S-28
- **ZA-02 · Distrito fuera del piloto.** Crear zona en Miraflores → `DISTRICT_NOT_IN_PILOT`. → ZN-01
- **ZA-03 · Un admin, una zona.** El admin de una zona intenta crear otra → `ALREADY_ADMIN`. → ZN-01, S-29
- **ZA-04 · Activar.** El admin registra la portería con el contacto "Sr. Ramos" → la zona queda `ACTIVA` y el vecino ya puede pedir. → ZN-02
- **ZA-05 · Activación inválida.** Un vecino que no es admin intenta activarla → `NOT_ZONE_ADMIN`. Con contacto vacío o tipo `VECINO` → `INVALID_RECEPTION`. → ZN-02
- **ZA-06 · Radio.** Un vecino a ≈ 250 m se une; otro a ≈ 450 m recibe `OUTSIDE_ZONE_RADIUS`. → ZN-03
- **ZA-07 · Cambio de zona con pedido activo.** Un vecino con pedido registrado en el ciclo intenta cambiarse → `HAS_ACTIVE_ORDER`. → ZN-03, S-30
- **ZA-08 · Unir zonas cercanas.** Dos zonas a ≈ 400 m: A pide y el admin de B acepta → mismo grupo, y en la liquidación 4 + 4 pedidos se atienden. → ZN-04, ZN-05
- **ZA-09 · Zonas lejanas.** Zonas a ≈ 1.5 km → `ZONES_TOO_FAR`. → ZN-04
- **ZA-10 · Sin cadena.** A (grupo con B) está a ≈ 400 m de B; C está a ≈ 400 m de B pero a ≈ 800 m de A → C no puede unirse al grupo: `ZONES_TOO_FAR`. → ZN-04, S-26
- **ZA-11 · Aceptación ajena.** Alguien que no es admin de B acepta la unión → `NOT_ZONE_ADMIN`. → ZN-05
- **ZA-12 · Salir del grupo.** El admin de A separa su zona → A vuelve a su propio grupo. → ZN-06
- **ZA-13 · Transferir admin.** El admin pasa el rol a un vecino de su zona → el nuevo admin puede activar o unir. Pasarlo a alguien de otra zona → `NOT_ZONE_MEMBER`. → ZN-07
- **ZA-14 · Unir fuera de ciclo.** Pedir unión el jueves → `CYCLE_CLOSED`. → ZN-04, S-31

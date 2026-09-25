# Iteración 18 · Cierre de huecos de robustez

## Requisito

Que el sistema no se quede trabado ni acepte datos absurdos en los casos que encontraron las revisiones de las iteraciones 12 y 16. Y que la demo sirva de punta a punta: hoy **nadie puede crear una zona ni unirse a una**, porque no hay forma de registrar la ubicación del vecino.

## Origen

Huecos reportados en `12-web-operacion.md` (1 a 7 y 9) y el que apareció al integrar la iteración 16: la web liquida sin exigir que las zonas estén entregadas.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-109 | El vecino registra su ubicación con latitud y longitud (la geocodificación de direcciones sigue fuera de alcance, S-27). | — |
| S-110 | Un vecino que es admin de su zona **no puede irse a otra** sin antes transferir el rol (refuerza S-29). | — |
| S-111 | Una solicitud de unión de zonas se puede **rechazar** (admin de la zona destino) o **retirar** (admin de la zona que la pidió). No puede haber dos solicitudes iguales pendientes. | — |
| S-112 | Las zonas y los vecinos del piloto tienen coordenadas de ejemplo en Lince, Jesús María, La Victoria y Miraflores, para que la demo funcione. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| HR-01 | Registrar la ubicación del vecino: latitud entre −90 y 90, longitud entre −180 y 180, ambas números finitos. | `INVALID_LOCATION` |
| HR-02 | Crear una zona valida el rango de las coordenadas del punto. | `INVALID_LOCATION` |
| HR-03 | Un admin de zona no puede unirse a otra zona (S-110). | `ADMIN_MUST_TRANSFER` |
| HR-04 | Solicitudes de unión: no se duplican; se pueden rechazar o retirar (S-111). | `MERGE_ALREADY_REQUESTED`, `NOT_ZONE_ADMIN`, `MERGE_REQUEST_NOT_FOUND` |
| HR-05 | Pedir devolución de saldo: monto numérico, mayor que 0, con hasta 2 decimales. Esto se valida en el caso de uso, no solo en la web. | `INVALID_AMOUNT` |
| HR-06 | Liquidar o cerrar un ciclo exige un identificador válido (`AAAA-Wnn`, con una semana que exista). | `INVALID_CYCLE` |
| HR-07 | Zonas y vecinos del piloto con coordenadas (S-112). | — |
| HR-08 | Web del admin: lista de devoluciones pendientes y registro de su pago con el código de operación (`mark_refund_paid`). | los de BS-13 |
| HR-09 | Web del admin: registrar una entrega fallida (`register_failed_delivery`). | los de EF-01..EF-03 |
| HR-10 | Web del admin: "Liquidar" usa `close_cycle` (EF-06): con zonas pendientes responde 422. **Cambia WA-10**, que ahora arma y entrega antes de liquidar. | `ZONES_PENDING` |

## Criterios de aceptación

- **HA-01 · Ubicación.** El vecino 101 registra (−12.0858, −77.0342) → queda guardada. Una latitud de 1000, una longitud de −200 o `nan` → `INVALID_LOCATION`. → HR-01
- **HA-02 · Crear zona con coordenadas malas.** Latitud 95 → `INVALID_LOCATION`. → HR-02
- **HA-03 · Admin que se va.** El admin de una zona intenta unirse a otra → `ADMIN_MUST_TRANSFER`. Después de transferir el rol, sí puede. → HR-03
- **HA-04 · Solicitudes de unión.** Pedir dos veces la misma unión → `MERGE_ALREADY_REQUESTED`. El admin destino la rechaza → desaparece. El admin origen retira otra → desaparece. Un tercero intenta rechazar → `NOT_ZONE_ADMIN`. → HR-04
- **HA-05 · Montos de devolución.** 0.001, 0, −5 y `abc` → `INVALID_AMOUNT`. 5.50 se acepta. → HR-05
- **HA-06 · Ciclo inválido.** `abc`, `2026-W99` y `2026-38` → `INVALID_CYCLE` al liquidar o cerrar. → HR-06
- **HA-07 · Demo de zonas.** Con los datos del piloto, el vecino 105 (de Z-LINCE-01, que vive a menos de 300 m del punto del condominio Z-LINCE-02) puede cambiarse a Z-LINCE-02. → HR-07
- **HA-08 · Pagar devolución desde la web.** El admin ve la devolución pendiente, registra el código `YP-1234` y queda `PAGADO`. → HR-08
- **HA-09 · Falla desde la web.** El admin registra `NADIE_RECIBE` con foto para una zona armada → queda registrada. → HR-09
- **HA-10 · Liquidar desde la web exige cerrar zonas.** Liquidar con una zona atendida sin entregar → 422 con `ZONES_PENDING`. Después de armar y entregar por la web → los pedidos quedan `LIQUIDADO`. → HR-10

## Cambios en criterios anteriores

- **OA-03 y OA-04** (`12-web-operacion.md`) usaban la zona piloto Z-LINCE-01 como ejemplo de "zona sin ubicación" (S-75). Con HR-07 las zonas del piloto tienen coordenadas. **La regla S-75 no cambia**: las pruebas ahora crean una zona antigua sin ubicación (`Z-SIN-UBICACION`) para verificarla.
- **WA-10** (`09-interfaz-web.md`): liquidar desde la web sin entregar ahora da `ZONES_PENDING` (HR-10). El camino completo está en HA-10.

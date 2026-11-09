# Yapa — CUS-04 Consolidar por zona y liquidar ("te devolvemos")

**Fuente de las reglas:** `api/docs/desarrollo/05-zonas-vecinos.md` (ZN), `api/docs/sdd/11-especificacion-liquidacion.md` (LQ), `16-entrega-fallida-cierre.md` (EF-04, EF-06) y `03-billetera-saldo.md` (BS-08..BS-11, BS-15). Decisiones C-02, C-06, C-07 y C-08.

## 0. Objetivo y frontera

Agrupar la demanda de los vecinos por zona (punto de recepción), decidir qué grupos llegan al mínimo de 8 pedidos y, después de la entrega, calcular cuánto costó cada pedido y devolver la diferencia como saldo.

Actores: **vecino** (crea su zona o se une), **admin de zona** (activa la recepción y une zonas, sin manejar dinero) y **administrador de Yapa** (cierra y liquida el ciclo).

## 1. Requerimientos funcionales

### Zonas

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-04.1 | Un vecino con ubicación crea una zona en un distrito piloto; nace `PENDIENTE_RECEPCION` y él queda como admin. | ZN-01 | Miraflores → `DISTRICT_NOT_IN_PILOT`; admin de otra zona → `ALREADY_ADMIN`. |
| RF-04.2 | El admin de zona la activa registrando la portería o el encargado y un contacto. | ZN-02 | Contacto vacío → `INVALID_RECEPTION`. Hasta activarla, los pedidos dan `ZONE_NOT_AVAILABLE`. |
| RF-04.3 | Un vecino se une a una zona si está a 300 m o menos del punto y no tiene pedido activo. | ZN-03 | A ≈ 450 m → `OUTSIDE_ZONE_RADIUS`; con pedido → `HAS_ACTIVE_ORDER`. |
| RF-04.4 | Dos admins unen sus zonas en un grupo si están a 500 m o menos de todas las del grupo, con el ciclo abierto. | ZN-04, ZN-05, S-26 | A ≈ 1,5 km → `ZONES_TOO_FAR`; sin cadenas. |
| RF-04.5 | El admin puede separar su zona y transferir su rol a un vecino de la zona. | ZN-06, ZN-07 | A alguien de otra zona → `NOT_ZONE_MEMBER`. |

### Liquidación

| ID | Requerimiento | Origen | Criterio de aceptación |
|---|---|---|---|
| RF-04.6 | Solo cuentan los pedidos con pago verificado; un grupo con menos de 8 queda `NO_ATENDIDO` y recibe el 100 % al medio de pago. | LQ-01, LQ-02, C-06 | 7 pedidos → reembolso total. |
| RF-04.7 | El tramo de cada producto se decide con la cantidad pedida entre todos los pedidos atendidos; el precio final nunca supera el máximo cobrado. | LQ-03, LQ-04, C-08 | 200 kg de papa en W39 → S/ 3,696 por kg. |
| RF-04.8 | El envío real es el costo de la parada ÷ pedidos de la zona, con tope de S/ 5. | LQ-05 | Parada de S/ 40 con 8 pedidos → S/ 5,00. |
| RF-04.9 | Los faltantes no se cobran; el saldo a favor = pagado − final, nunca negativo, se abona a la billetera. | LQ-06..LQ-08, BS-08 | El pedido queda `LIQUIDADO`. |
| RF-04.10 | El ciclo solo se cierra cuando cada zona atendida está entregada o fallida; la liquidación es todo o nada y una sola vez. | EF-06, BS-11, BS-15 | Zona pendiente → `ZONES_PENDING`; liquidar dos veces → `CYCLE_ALREADY_SETTLED`. |
| RF-04.11 | El resumen muestra el tramo alcanzado y el precio final de cada producto, el total devuelto y el reembolsado. | LQ-09 | Visible para el vecino en Mi cuenta ("Te devolvemos"). |

## 2. Ficha

| Campo | Descripción |
|---|---|
| Identificador | CUS-04 |
| Actores | Vecino, admin de zona, administrador de Yapa |
| Disparador | Zonas: un vecino quiere pedir y no hay zona activa cerca. Liquidación: todas las zonas del ciclo fueron entregadas o fallaron. |
| Precondiciones | Liquidación: ciclo cerrado, entregas registradas (CUS-07), faltantes reportados. |
| Postcondición de éxito | Cada pedido queda `LIQUIDADO`, `NO_ATENDIDO`, `NO_ENTREGADO` o `CANCELADO`, con su saldo o reembolso; la conciliación sigue en 0. |
| Garantía ante fallo | Si el reporte de faltantes es inválido, no cambia ningún estado ni saldo (BS-15). |

## 3. Flujo principal (cerrar y liquidar)

| Paso | Administrador | Sistema |
|---|---|---|
| 1 | Abre "Liquidar" y elige el ciclo. | Muestra el estado de cada zona (entregada, fallida o pendiente). |
| 2 | Confirma el cierre. | Verifica que no haya zonas pendientes (EF-06). |
| 3 | — | Cancela los pedidos sin pago verificado, aplica el mínimo por grupo, calcula tramos, envío real y faltantes. |
| 4 | — | Abona el saldo de cada pedido, registra reembolsos y avisa a cada vecino. |
| 5 | Ve el resumen. | Muestra tramos, precios finales, total devuelto y reembolsado. |

### Subflujo: crear y activar una zona

| Paso | Actor | Sistema |
|---|---|---|
| 1 | El vecino toca "Usar mi ubicación" y crea la zona. | Valida distrito y ubicación; la zona queda `PENDIENTE_RECEPCION`. |
| 2 | Como admin de zona, registra la portería y el contacto. | La zona queda `ACTIVA` y sus vecinos ya pueden pedir. |
| 3 | Invita a sus vecinos con su enlace. | Los que se registran por ese enlace quedan en la zona. |

## 4. Flujos alternativos y excepciones

| Código | Condición | Respuesta |
|---|---|---|
| FA-01 | El grupo no llega a 8 pedidos verificados. | Pedidos `NO_ATENDIDO`; reembolso del 100 % al medio de pago. |
| FA-02 | La entrega de una zona falló (CUS-07). | Pedidos `NO_ENTREGADO`: se cobra solo el envío real y el resto vuelve como saldo; sus cantidades cuentan para los tramos (EF-04). |
| FA-03 | Una zona sigue pendiente. | `ZONES_PENDING` con el nombre de la zona; nadie recibe saldo todavía. |
| FA-04 | Faltante inválido (más que lo pedido, producto ajeno). | `INVALID_MISSING_ITEM`; no cambia nada. |
| EX-01 | El ciclo ya se liquidó. | `CYCLE_ALREADY_SETTLED`. |

## 5. Escenarios de aceptación

1. **Unir zonas.** Dos zonas a ≈ 400 m con 4 pedidos cada una se unen → el grupo suma 8 y ambas se atienden. (ZA-08)
2. **Sin cadena.** C está a 400 m de B pero a 800 m de A (grupo A+B) → `ZONES_TOO_FAR`. (ZA-10)
3. **Liquidación con tramos.** En W39, con 200 kg de papa entre todos (tramo desde 100 kg), el precio final es 3,30 × 1,12 = S/ 3,696. (CT-L)
4. **Entrega fallida.** Parada de S/ 40 con 8 pedidos → cada uno paga S/ 5,00 de envío y recupera S/ 56,00 como saldo. (EF-B)
5. **Cierre con zona pendiente.** → `ZONES_PENDING`; con todas cerradas, liquida igual que el cálculo puro. (EF-E, EF-F)

## 6. Pantallas y código

- Web: página de la zona (`ZonePage.tsx`, mapa `ZonesMap.tsx`), panel → Zonas, Análisis y Liquidar; Mi cuenta → "Te devolvemos".
- API: `/api/zonas/*`, `/api/solicitudes/*`, `/api/mi-zona`, `/api/admin/analisis`, `/api/admin/ciclos/{ciclo}/liquidar`.
- Motor: `zones.py`, `settlement.settle_cycle`, `fulfillment.close_cycle`, `wallet.py`.

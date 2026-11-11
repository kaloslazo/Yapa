# Iteración 62 · El vecino ve el avance de su grupo en la semana

## Requisito

Como vecino, quiero ver en el Inicio cuántos pedidos lleva mi grupo esta semana frente a los 8 que hacen falta. Así sé si vamos a comprar juntos y me animo a pedir o a avisar a mis vecinos.

## Por qué

La estructura nueva de la tienda (aprobada el 10/11/2026) pone en la tarjeta de la semana «Tu edificio lleva 5 de 8 pedidos para comprar juntos» con una barra. Hasta ahora el motor solo daba ese avance al admin de zona (AZ-08, iteración 28). El cálculo es el mismo; cambia quién lo ve y cuánto ve.

Va en `GET /api/mi-zona` y no en `/api/estado`: `/api/estado` es público y no sabe quién pregunta, y el avance depende de la zona del vecino, así que pide sesión.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-320 | Cualquier vecino con zona ve el avance de su grupo en la semana: cuántos pedidos con pago verificado llevan las zonas de su mismo grupo, sin los cancelados, frente al mínimo de 8 (S-06). Es el mismo número que ve el admin de zona (AZ-08). **Solo el conteo**: ni nombres, ni montos, ni ubicaciones (S-165, Ley 29733). | — |
| S-321 | La tienda muestra la línea en la tarjeta de la semana solo mientras el ciclo está abierto: después del miércoles 8 p. m. ya nadie puede sumarse. Con 8 o más dice que el edificio ya llegó. Sin sesión o sin zona, la tarjeta queda como estaba. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AG-01 | `GET /api/mi-zona` trae `avance` con `verificados`, `minimo` y `ciclo` para el vecino que tiene zona. Sin zona, `avance` es `null`. | — |
| AG-02 | `verificados` cuenta los pedidos del ciclo actual con pago `VERIFICADO` de cualquier zona del mismo grupo, sin los `CANCELADO_POR_CLIENTE`. Lo calcula la misma función que usa el panel del admin de zona (AZ-08). | — |
| AG-03 | `avance` trae solo esos tres campos (S-165). | — |
| AG-04 | Sin sesión, `GET /api/mi-zona` sigue respondiendo 401. | `LOGIN_REQUIRED` |

## Criterios de aceptación

Semana 2026-W38, miércoles 16/09 a las 10:00. Z-LINCE-01 y Z-LINCE-02 están en el mismo grupo; Z-JM-01 está en otro.

- **AG-A · Vecina que no administra.** Ana (101) y Carmen (105), de Z-LINCE-01, y el vecino 130, de Z-LINCE-02, tienen su pedido de S/ 61.00 con pago verificado. Carmen recibe `avance` = `{"verificados": 3, "minimo": 8, "ciclo": "2026-W38"}` y `administra` sigue en `null`. → AG-01, AG-02
- **AG-B · Lo que no cuenta.** Además del caso AG-A: el vecino 120 (Z-LINCE-01) registra su pedido y no paga; el 121 (Z-LINCE-01) paga, se le verifica y cancela; el 801 (Z-JM-01) paga y se le verifica; y Ana tuvo un pedido verificado la semana anterior (2026-W37). Carmen sigue viendo 3 de 8. → AG-02
- **AG-C · Solo el conteo.** `avance` tiene exactamente `verificados`, `minimo` y `ciclo`. → AG-03, S-165
- **AG-D · Sin zona.** Un vecino cuya zona no existe recibe `avance` = `null`. → AG-01
- **AG-E · El mismo número que el admin.** Si Ana administra Z-LINCE-01, su `avance` es igual a `administra.avance` (3 de 8). → AG-02
- **AG-F · Sin sesión.** `GET /api/mi-zona` sin entrar → 401 `LOGIN_REQUIRED`. → AG-04
- **AG-G · Tienda.** Con el ciclo abierto y 5 de 8, la tarjeta de la semana dice «Tu edificio lleva 5 de 8 pedidos para comprar juntos» y la barra llega al 62,5 %. Con 9 dice «Tu edificio ya llegó a los 8 pedidos para comprar juntos» y la barra queda llena. Sin avance (sin sesión o sin zona) o con el ciclo cerrado, no aparece. → S-321

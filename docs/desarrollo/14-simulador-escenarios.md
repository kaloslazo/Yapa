# Iteración 14 · Simulador de escenarios para decidir comisión y mínimo de zona

## Requisito

Como equipo de Yapa, queremos saber **con cuántos pedidos por zona, qué comisión y qué medio de cobro dejamos de perder plata**, para responder las decisiones urgentes 1 y 2 de `supuestos-a-validar.md` con números y no a ojo.

## Cómo

El simulador arma un ciclo sintético con las **mismas reglas del sistema**: registro, liquidación por tramos, envío compartido y margen neto (iteración 13). No es una hoja de cálculo paralela: si cambia una regla, el simulador la usa automáticamente.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-98 | La canasta tipo del simulador es la de las pruebas de liquidación: 5 kg de papa amarilla, 10 kg de papa blanca y 10 kg de cebolla (S/ 61.00 pagados). Se puede cambiar. | — |
| S-99 | Se simula una sola zona (sin zonas unidas), con todos los pedidos iguales y pagados por medio externo. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| SM-01 | `simulate(pedidos, costo de parada, comisión de frescos, escenario de costos)` devuelve el margen neto promedio por pedido y el ahorro promedio que vuelve al cliente, calculados con las reglas del sistema. | — |
| SM-02 | Simular no modifica nada del sistema real: la comisión de la simulación se aplica solo durante la simulación, y después vuelve a su valor. | — |
| SM-03 | `break_even_orders(costo de parada, comisión, escenario)` devuelve el **mínimo de pedidos por zona** para que el margen neto promedio no sea negativo, buscando entre 8 y 60. Si ni con 60 alcanza, devuelve "no alcanza". | — |
| SM-04 | Hay una tabla para el equipo: margen neto por número de pedidos (8, 12, 16, 20) y comisión (10 %, 12 %, 15 %), en los dos escenarios. | — |

## Criterios de aceptación

- **SA-01 · Coincide con la iteración 13.** Con 8 pedidos, parada de S/ 40 y 12 %: pesimista −S/ 1.8195 y optimista S/ 3.31. → SM-01
- **SA-02 · Más pedidos, mejor margen.** Con 20 pedidos, el margen neto pesimista es mayor que con 8, y el ahorro para el cliente también es mayor. → SM-01
- **SA-03 · No toca el sistema.** Después de simular con 15 %, la comisión real de frescos sigue en 12 %. → SM-02
- **SA-04 · Punto de equilibrio.** En el escenario optimista, con parada de S/ 40 y 12 %, el mínimo es 8 pedidos. En el pesimista, el mínimo es mayor que 8 o "no alcanza". → SM-03
- **SA-05 · Tabla.** La tabla tiene 4 × 3 celdas por escenario, y la celda (8 pedidos, 12 %) coincide con SA-01. → SM-04

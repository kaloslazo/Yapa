# Iteración 15 · Parte del ahorro por volumen que retiene Yapa (opción A)

## Requisito

Como equipo, queremos poder probar la **opción A** de la decisión urgente n.º 5 (que Yapa se quede con una parte del ahorro por volumen) y ver cuánto cambia el margen y el ahorro del cliente. Esto **no cambia el modelo actual** mientras el equipo no lo decida.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-100 | "Parte retenida" = fracción del ahorro por volumen (precio máximo − precio del tramo) que se queda Yapa. **Por defecto es 0**, que es el modelo actual (C-02: todo vuelve al cliente). | 0 |
| S-101 | La parte retenida no afecta el envío compartido: lo que sobra del envío sigue volviendo entero al cliente. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| RA-01 | Precio final por unidad = precio del tramo + parte × (precio máximo − precio del tramo). Con parte 0 da exactamente lo mismo que LQ-04. | — |
| RA-02 | La parte debe estar entre 0 y 1. | `INVALID_SAVINGS_SHARE` |
| RA-03 | Con cualquier parte válida, el precio final nunca pasa del precio máximo: se mantiene C-01. | — |
| RA-04 | El simulador acepta la parte retenida, y `savings_share_table` muestra el margen neto y el ahorro del cliente con 0 %, 25 % y 50 %. | — |

## Criterios de aceptación

Escenario: 20 pedidos, parada de S/ 40, comisión de 12 %, costos pesimistas.

- **RA-A · Sin cambio por defecto.** Con parte 0, la liquidación da los mismos montos que en la iteración 2 (CL-04: final S/ 48.14, saldo S/ 12.86). → RA-01
- **RA-B · Con 50 %.** El precio final de la papa amarilla con 100 kg es 3.7856 + 0.5 × (4.032 − 3.7856) = **S/ 3.9088**. El margen neto pesimista promedio sube a **≈ S/ 2.41** y el ahorro del cliente baja a **≈ S/ 7.93** (±S/ 0.01 por el redondeo al céntimo a favor del cliente). → RA-01, RA-04
- **RA-C · Parte inválida.** −0.1 o 1.5 → `INVALID_SAVINGS_SHARE`. → RA-02
- **RA-D · Nunca más que el máximo.** Con parte 1, el precio final es igual al precio máximo y el cliente recupera solo el envío. → RA-03
- **RA-E · No toca el sistema real.** Después de simular con 50 %, una liquidación normal usa parte 0. → RA-04, SM-02

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
- **SA-02 · Más pedidos: más ahorro para el cliente, pero no más margen para Yapa.** Con 20 pedidos, el ahorro promedio del cliente es mayor que con 8 (S/ 12.86 frente a S/ 3.36), pero el margen neto pesimista es **menor** (−S/ 2.52 frente a −S/ 1.82). → SM-01
  - *Corrección de la spec:* la primera versión decía "más pedidos, mejor margen". Al correr la prueba con las reglas reales, eso resultó **falso** (ver "Hallazgo" abajo). Se corrigió la spec antes de tocar el código; la prueba no se debilitó, se reescribió según el comportamiento verdadero.
- **SA-03 · No toca el sistema.** Después de simular con 15 %, la comisión real de frescos sigue en 12 %. → SM-02
- **SA-04 · Punto de equilibrio.** En el escenario optimista, con parada de S/ 40 y 12 %, el mínimo es 8 pedidos. En el pesimista, **no alcanza con ningún número de pedidos** (el margen baja con el volumen). → SM-03
- **SA-05 · Tabla.** La tabla tiene 4 × 3 celdas por escenario, y la celda (8 pedidos, 12 %) coincide con SA-01. → SM-04

## Hallazgo de negocio (al correr el simulador)

**Hoy, que el grupo crezca no mejora el margen de Yapa: lo empeora.**

| Pedidos en la zona | Margen neto optimista | Margen neto pesimista | Ahorro del cliente |
|---|---|---|---|
| 8 | S/ 3.31 | −S/ 1.82 | S/ 3.36 |
| 12 | S/ 3.16 | −S/ 1.97 | S/ 6.37 |
| 20 | S/ 2.61 | −S/ 2.52 | S/ 12.86 |
| 30 | S/ 2.52 | −S/ 2.61 | S/ 14.42 |

**Por qué pasa:**

- Todo el descuento por volumen vuelve al cliente como saldo (C-02).
- La comisión de Yapa es un porcentaje del precio **final**, que baja con el volumen.
- El envío compartido solo recupera el costo de la parada, sin ganancia.
- Los costos operativos por pedido (armado, atención, cobro) no bajan.

**Qué debería decidir el equipo** (se agrega como decisión urgente n.º 5):

- **Opción A:** que Yapa se quede con una parte del ahorro por volumen. Por ejemplo, la comisión se calcula sobre el precio del primer tramo y no sobre el final. El cliente sigue ahorrando, pero un poco menos.
- **Opción B:** cobrar un fee fijo por pedido además del porcentaje.
- **Opción C:** mantener el modelo y bajar costos: Plin en vez de Yape Empresa, y que el proveedor entregue. Con eso, el escenario optimista deja entre S/ 2.5 y S/ 3.3 por pedido.

Con el simulador (`python -m yapa_sdd.simulator 40`) se puede probar cada opción cuando se decida.

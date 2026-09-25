# Iteración 13 · Margen neto con costos operativos (escenarios)

## Requisito

Como equipo de Yapa, queremos ver si cada pedido **realmente deja plata** después de armarlo, cobrarlo y atenderlo, no solo después de pagar al proveedor y la parada. Así evitamos el error de Favo: crecer sin margen por pedido.

## Por qué

La iteración 8 midió el **margen de contribución** (S-49), que no incluye costos operativos. Su escenario base da **S/ 5.64** por pedido. Pero en `docs/analisis/08_validacion_economica.md` medimos costos operativos de entre S/ 3.22 y S/ 12.69 por pedido. Este es el hallazgo urgente n.º 1 de `supuestos-a-validar.md`.

**Esta iteración no decide cuál es el costo real** (eso lo decide el equipo). Muestra el resultado en los dos escenarios que ya están documentados con fuentes.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-95 | Los costos operativos por pedido son: viaje de compra (S/ por pedido), armado (S/ por pedido), atención (S/ por pedido) y comisión de cobro (% del monto pagado **por Yape/Plin**; lo pagado con saldo no paga comisión). La entrega **no** se suma aquí, porque ya está en la parada (S-49). | — |
| S-96 | Escenario **optimista**: el proveedor entrega (viaje S/ 0), armado S/ 1.60, atención S/ 0.73, cobro por Plin negocios 0 %. | de `08_validacion_economica.md` |
| S-97 | Escenario **pesimista**: viaje de compra S/ 3.33, armado S/ 1.60, atención S/ 0.73, cobro por Yape Empresa 2.95 %. | de `08_validacion_economica.md` |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| NM-01 | Costo operativo de un pedido = viaje + armado + atención + comisión × lo pagado por medio externo. | — |
| NM-02 | Margen neto = margen de contribución (MT-02) − costo operativo. Solo pedidos liquidados; el ciclo debe estar liquidado (MT-01). | `CYCLE_NOT_SETTLED` |
| NM-03 | El resumen por escenario da: número de pedidos, margen neto promedio, cuántos pedidos pierden plata y **cuánto faltaría por pedido** para no perder (promedio de lo que les falta a los negativos). | — |
| NM-04 | Los escenarios se pueden cambiar sin tocar el código: son datos (`OperatingCosts`). | — |

## Criterios de aceptación

Escenario MT-A: 8 pedidos en Jesús María, cada uno pagado con S/ 61.00 por Yape, margen de contribución de S/ 5.64.

- **NA-01 · Optimista.** Costo operativo = 0 + 1.60 + 0.73 + 0 % × 61.00 = **S/ 2.33**. Margen neto = **S/ 3.31** por pedido. Ningún pedido pierde. → NM-01, NM-02
- **NA-02 · Pesimista.** Costo operativo = 3.33 + 1.60 + 0.73 + 2.95 % × 61.00 = **S/ 7.4595**. Margen neto = **−S/ 1.8195** por pedido. Los 8 pierden, y faltarían S/ 1.8195 por pedido. → NM-01..NM-03
- **NA-03 · El saldo no paga comisión.** Un pedido de S/ 61.00 pagado con S/ 10 de saldo y S/ 51 por Yape: la comisión pesimista es 2.95 % × 51 = S/ 1.5045, no sobre 61. → NM-01, S-95
- **NA-04 · Sin liquidar.** Pedir el resumen de un ciclo sin liquidar → `CYCLE_NOT_SETTLED`. → NM-02
- **NA-05 · Escenario propio.** Con un escenario de armado S/ 1.00, sin viaje, sin atención y sin comisión, el margen neto es S/ 4.64. → NM-04

## Qué debería decidir el equipo con esto

Si el escenario pesimista se parece a la realidad, **cada pedido pierde plata**. Se puede corregir con:

- cobrar con Plin negocios (0 %) en vez de Yape Empresa;
- conseguir que el proveedor entregue (así desaparece el viaje);
- subir la comisión;
- o subir el mínimo de pedidos por zona.

Esta iteración da los números para decidir; no decide.

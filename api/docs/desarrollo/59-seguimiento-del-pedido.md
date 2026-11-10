# Iteración 59 · Seguimiento del pedido: dónde está tu compra, tu pago y tu reparto

## Requisito

Como vecino, quiero ver en una sola pantalla en qué va mi pedido: si mi pago se verificó, si ya se compró, si mi bolsa está armada, si el reparto salió, quién lo recibió y cuánto me devolvieron, con la hora y la evidencia de cada paso.

## Por qué

En la revisión del 09/11/2026, con el celular, salió esto:

- La línea de 7 pasos de la iteración 58 se parte en dos filas y no se entiende como un recorrido.
- No hay horas ni evidencias. El vecino no sabe a qué hora salió el reparto, quién recibió ni si la portería confirmó.
- Mientras el pago está pendiente, no hay una tarjeta clara de cuánto, a dónde y con qué código.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-310 | El pedido guarda la hora en que se registró. La hora del pago verificado es la del registro de caja (S-114). Si se pagó todo con saldo, es la hora del registro del pedido. Los pedidos guardados antes de esta iteración no tienen hora de registro y la muestran vacía. | — |
| S-311 | **Resumen en una frase**, según el último paso hecho. La entrega es el **sábado del ciclo** (lunes de apertura + 5 días). | ver SG-02 |
| S-312 | **Detalle por paso.** Pago: medio y monto. Comprado: lo que le faltó a **este** pedido y si lo repuso el colchón o vuelve como saldo. Armado: cuántas bolsas. En camino: a qué zona y a qué hora salió. Entregado: quién recibió y, si la portería confirmó, a qué hora. Te devolvemos: cuánto volvió a su saldo. | — |
| S-313 | **Fotos del propio pedido.** El vecino ve las fotos de sus bolsas y de la entrega de su zona, y solo de su pedido. La ruta del archivo sale del registro del sistema, nunca de lo que manda el navegador. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| SG-02 | El seguimiento trae `estado`: un título y un detalle de una frase (S-311). Pedido cancelado por el vecino: "Cancelaste este pedido". Anulado: "Anulado: el pago no llegó antes del cierre". Sin mínimo: "Tu grupo no llegó a 8 pedidos". No entregado: "No se pudo entregar". Por verificar: "Falta tu pago". Verificado: "Pago verificado". Comprado: "Comprado". Armado: "Armado". En camino: "En camino a {zona}". Entregado: "Entregado en {zona}". Liquidado: "Te devolvimos S/ X". | — |
| SG-03 | Cada paso trae `hecho`, `cuando` (ISO 8601 o vacío) y `detalle` (S-312). | — |
| SG-04 | `GET /api/pedidos/{id}/fotos/{cual}` con `cual` = `entrega` o `bolsa-N`: solo el dueño del pedido. | `ORDER_NOT_FOUND` (404), `PHOTO_NOT_FOUND` (404) |
| SG-05 | El seguimiento dice cuántas fotos hay (`fotos`: `entrega` y `bolsas`) para que la web las muestre. | — |

## Criterios de aceptación

Escenario base: W38, Z-JM-01 (Residencial San Felipe), 8 pedidos registrados el miércoles 16/09 a las 10:00 y verificados en ese momento. Pedido 1 = 5 kg de papa amarilla, 10 kg de papa blanca, 10 kg de cebolla roja.

- **SG-A · Por verificar.** Un pedido recién registrado y sin verificar → estado "Falta tu pago". Paso Pedido hecho, con hora 16/09 10:00. Pago verificado sin hacer. → SG-02, SG-03, S-310
- **SG-B · Verificado.** Estado "Pago verificado", con detalle "Compramos el jueves y entregamos el sábado 19/09". El paso Pago verificado tiene hora 16/09 10:00 y detalle "Yape · S/ 61.00". → SG-02, S-311
- **SG-C · Comprado con faltante.** La compra llega con 36 kg de papa amarilla. En el pedido 8, el paso Comprado dice "Faltó 4 kg de Papa amarilla: vuelve como saldo". En el pedido 1 dice "Llegó todo". → S-312
- **SG-D · Armado y en camino.** Con 2 bolsas, el paso Armado dice "2 bolsas, con foto". Al marcar la salida el sábado 19/09 a las 09:00, el estado es "En camino a Residencial San Felipe" y el paso En camino tiene hora 19/09 09:00. → SG-02, S-312
- **SG-E · Entregado y recibido.** Al entregar a "Sr. Ramos" y confirmar la portería, el estado es "Entregado en Residencial San Felipe". El detalle dice "Lo recibió Sr. Ramos" y "La portería lo confirmó". `fotos` = {entrega: true, bolsas: 2}. → SG-02, S-312, SG-05
- **SG-F · Liquidado.** Después de liquidar, el estado es "Te devolvimos S/ X", con X = lo devuelto a su saldo. → SG-02
- **SG-G · Estados finales.** Cancelado por el vecino, anulado, sin mínimo y no entregado dan sus títulos de SG-02. → SG-02
- **SG-H · Fotos.** El dueño obtiene la foto de la entrega y la de la bolsa 1 (200). Otro vecino recibe 404 `ORDER_NOT_FOUND`. `bolsa-9` o `cualquiera` dan 404 `PHOTO_NOT_FOUND`. → SG-04, S-313

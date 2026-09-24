# Clarificaciones · iteración 2

Este documento se escribió **antes** de tocar código. Registra las ambigüedades y huecos que encontramos al revisar la primera versión de la spec contra el modelado de negocio (Entregable 1), la idea inicial del proyecto y datos reales de precios. Cada decisión dice quién la tomó y en qué fuente se apoya.

## Por qué hubo una segunda iteración

1. **Problema legal en el cobro.** El Entregable 1 cobraba en la puerta un saldo cuando el peso real salía mayor, y retenía el pedido si el cliente no pagaba. La Ley 29571 (art. 4.2) prohíbe obligar al consumidor a pagar recargos sobre el precio fijado.
2. **Se compraba antes de saber quién había pagado.** El cierre era el miércoles a las 20:00 y las transferencias se verificaban hasta el jueves a las 12:00, pero el mercado mayorista opera de madrugada.
3. **Se repetía el patrón de proyectos que fracasaron.**
   - Favo agrupaba por distrito, sin mínimo de activación y sin control del margen por pedido.
   - Muni y Meituan dependían de subsidios.
   - Merqueo y Missfresh cargaban con inventario propio.
4. **El margen no alcanzaba con abarrotes de marca.**
   - Los precios reales (24/09/2026) dan una brecha supermercado–mayorista de solo **6.5 %**.
   - En frescos resistentes la brecha llega a **36–67 %**.
   - Ver `docs/analisis/08_validacion_economica.md`.
5. **La spec y el código no coincidían** en 14 casos borde (ver `docs/analisis/02_discordancias_spec_codigo.md`).

## Decisiones del modelo (equipo)

| # | Decisión | Quién / fecha |
|---|---|---|
| C-01 | **Precio máximo garantizado**: el cliente nunca paga más de lo que vio al registrar. | Carlos, 23/09 |
| C-02 | **Todos pagan el precio máximo** y el ahorro se liquida después de la entrega ("te devolvemos"). Si alguien cancela, solo baja el ahorro estimado de los demás; Yapa nunca pierde. | Carlos y Kalos, 24/09 |
| C-03 | **Solo pago anticipado** con Yape o Plin. Se elimina la contraentrega. | Carlos, 23/09 |
| C-04 | El pago se confirma con el **código de operación** del comprobante de Yape o Plin, que no puede repetirse entre pedidos. | Carlos, 24/09 |
| C-05 | El **ahorro vuelve como saldo a favor**. No vence y el cliente puede pedir que se le devuelva a su medio de pago (hasta 30 días). | Carlos, 23/09 |
| C-06 | Si la zona **no llega al mínimo**, se devuelve el 100 % al medio de pago, sin opción de saldo. | Carlos, 23/09 |
| C-07 | **Zona** = punto de recepción (portería o encargado) creado por un vecino admin, con radio máximo. Zonas cercanas pueden unirse y cuentan juntas para el mínimo, pero cada una tiene su propia parada. | Carlos, 23–24/09 |
| C-08 | El **descuento por volumen** depende de la cantidad total que compra Yapa de ese producto. El **envío** se reparte entre los pedidos de cada zona. | Carlos, 24/09 |
| C-09 | **Envío compartido con tope**: se paga el máximo y lo que sobra vuelve como saldo. | Carlos, 23/09 |
| C-10 | Los artículos faltantes o dañados se devuelven **por artículo**, no por pedido completo. | Carlos, 24/09 |
| C-11 | **Catálogo piloto corto**: frescos resistentes y limpieza de marcas emergentes, una sola marca por producto, frescos en pasos fijos de kg. | Carlos, 24/09 |
| C-12 | El proveedor aliado entrega su lista semanal con precios por tramo **y la cantidad máxima que puede vender**. Nunca se vende más de eso. | Carlos, 23/09 |

## Supuestos del equipo (propuestos, a validar por Kalos y Aaron)

Son valores concretos que la spec necesita para ser verificable. Si cambian, se cambian aquí primero.

| # | Supuesto | Valor |
|---|---|---|
| S-01 | Distritos piloto | Lince, Jesús María, La Victoria |
| S-02 | Recepción de pedidos | Desde el lunes 00:00 hasta **antes** del miércoles 20:00. Las 20:00:00 exactas ya están fuera. Hora de Lima. |
| S-03 | Pedidos por cliente | Uno por cliente por ciclo |
| S-04 | Pedido mínimo individual | S/ 50.00, calculado sobre el subtotal exacto, sin redondear |
| S-05 | Envío máximo por pedido | S/ 5.00 |
| S-06 | Mínimo de zona | 8 pedidos con pago verificado (las zonas unidas suman) |
| S-07 | Comisión de servicio | Frescos 12 %, limpieza 9 % |
| S-08 | Cantidades | Productos por kg en múltiplos de su paso (1 kg; ajo 0.25 kg). Productos por unidad en enteros. Tope por línea: 10 kg o 6 unidades. |
| S-09 | Redondeo | Los cálculos son exactos. El monto final se redondea al céntimo **a favor del cliente** (Ley 29571, art. 44). |
| S-10 | Ventana de entrega | La asigna Yapa a cada zona. El cliente no la elige, porque recibe la portería. |

## Fuera de alcance de esta iteración (con motivo)

- **Persistencia real, web y autenticación.** No cambian las reglas que se demuestran; se usa un repositorio en memoria y una CLI.
- **Integración con Yape o Plin.** No tienen API pública directa. La verificación del código de operación la hace el administrador; aquí se simula.
- **Crear y unir zonas desde un mapa.** La zona llega ya definida como dato de entrada.
- **Cancelación y edición de pedidos, compra al proveedor, armado y ruteo.** Son otros casos de uso.
- **Comprobante electrónico, Libro de Reclamaciones y autorización sanitaria (SENASA / local).** Son requisitos legales pendientes. El proyecto es académico y no se lanza.

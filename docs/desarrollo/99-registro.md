# Registro de iteraciones de desarrollo

## Iteración 3 · Billetera de saldo (24/09/2026)

- Spec: `03-billetera-saldo.md`. Se agregan los supuestos S-13..S-17, que el equipo debe validar.
- Pruebas antes del código: `docs/evidencia/desarrollo/03-billetera-rojo.txt`.
- Diseño: `Order` pasa a tener una lista de pagos (saldo + Yape/Plin), se crea el módulo `wallet.py`, y la liquidación abona saldo y registra reembolsos.
- En la revisión apareció una regla nueva, **BS-15 "todo o nada"**: la liquidación aplicaba efectos (estados) antes de validar el reporte de faltantes. Se reordenó para validar primero y aplicar después.
- Resultado: 61 pruebas en verde. Las de la iteración 2 siguen pasando sin cambios.
- Nota: las líneas de código citadas en `docs/sdd/06-trazabilidad.md` corresponden al checkpoint del Lab 4 (tag `checkpoint-lab4`).

## Iteración 4 · Cancelar y editar (24/09/2026)

- Spec: `04-cancelar-editar.md`, con los supuestos S-18..S-24.
- Pruebas antes del código: `docs/evidencia/desarrollo/04-cancelar-editar-rojo.txt`.
- **Hallazgo de seguridad al diseñar:** editar un pedido a la baja habría convertido en saldo real un pago **sin verificar**, lo que permitía cobrar con un código de operación falso. Se especificó S-24/CE-12, se agregó la prueba CE-H y recién después se implementó.
- Implementación: módulo `order_changes.py`. "Un pedido por ciclo" pasa a significar "un pedido **activo**" (`store.find_order`), y la liquidación ignora los pedidos cancelados por el cliente.
- Resultado: 79 pruebas en verde.

## Iteración 5 · Zonas de vecinos (24/09/2026)

- Spec: `05-zonas-vecinos.md`, con los supuestos S-25..S-32 (radio de 300 m, unión a 500 m sin cadenas, activación por portería o encargado).
- Pruebas antes del código: `docs/evidencia/desarrollo/05-zonas-rojo.txt`.
- Al revisar las pruebas se corrigió un dato del ZA-07: el vecino quedaba a exactamente 300 m de la otra zona, así que la prueba dependía de un redondeo. Se movió a 150 m y 250 m.
- Implementación: módulo `zones.py`. `Zone` ahora tiene coordenadas, admin y datos de recepción, y `Customer` tiene ubicación opcional.
- Resultado: 94 pruebas en verde.

## Iteración 6 · Catálogo semanal del proveedor aliado (24/09/2026)

- Spec: `06-catalogo-semanal.md`, con los supuestos S-33..S-37, S-38 (orden de los errores al publicar) y S-39 (editar con un producto desactivado), todos a validar por el equipo.
- Pruebas antes del código: `docs/evidencia/desarrollo/06-catalogo-rojo.txt` (9 errores: el módulo no existía y las reservas no tenían ciclo).
- Implementación: módulo `catalog.py` (`publish_catalog`, `deactivate_product`). El store guarda un catálogo por ciclo, los administradores y los proveedores; las reservas pasan a ser por ciclo, lo que corrige la limitación anotada en la iteración 3. `Product` tiene `supplier_id` opcional y `cycle.opens_at` da el lunes 00:00 del ciclo.
- Se anotaron en la spec cuatro huecos para el equipo (editar un pedido con un producto desactivado, desactivar en el catálogo base, unidad y paso sin validar, proveedor que deja de ser aliado).
- Resultado: 106 pruebas en verde (`docs/evidencia/desarrollo/06-catalogo-verde.txt`).
- **Revisión:** editar un pedido con un producto desactivado rechazaba toda la edición. Se especificó S-39/CT-11 (la línea desactivada se mantiene con la misma cantidad o menos), se agregó la prueba CT-M en rojo (`06-catalogo-edicion-rojo.txt`) y después el código. Resultado: 107 pruebas en verde.

## Iteración 7 · Armado, entrega en portería, reclamos por artículo y colchón (24/09/2026)

- Spec: `07-armado-entrega-reclamos.md`, con los supuestos S-40..S-46, a validar por el equipo (personal = administradores, entrega por zona todo o nada, plazo de 24 h, aprobación con el ciclo liquidado, colchón de S/ 500 solo con limpieza).
- Pruebas antes del código: `docs/evidencia/desarrollo/07-armado-entrega-rojo.txt`.
- Implementación: módulos `fulfillment.py` (bolsas y entrega), `claims.py` (reclamo y revisión) y `buffer.py` (colchón). La liquidación guarda su resultado en `store.settlements` para que el reclamo aprobado use el precio final del artículo.
- **Decisión de diseño para no devolver dos veces:** un faltante que ya se descontó en la liquidación no se puede aprobar otra vez como reclamo (RV-04, criterio RV-E).
- Se anotaron cinco huecos para el equipo en la spec.
- Resultado: 132 pruebas en verde (`docs/evidencia/desarrollo/07-armado-entrega-verde.txt`).

## Iteración 8 · Métricas del piloto (24/09/2026)

- Spec: `08-metricas-piloto.md`, con los supuestos S-47..S-52, a validar por el equipo (qué cuenta como compra, cohorte por primera compra con meta del 50 %, margen de contribución sin costos operativos, ahorro sin faltantes ni reclamos).
- Pruebas antes del código: `docs/evidencia/desarrollo/08-metricas-rojo.txt`.
- Implementación: módulo `metrics.py`, que solo lee la liquidación guardada, los pedidos y los reclamos. `cycle.add_weeks` calcula el ciclo N + 3.
- Hallazgo: con una parada de S/ 100 y 8 pedidos, el tope de envío de S/ 5 deja cada pedido con margen negativo (−S/ 1.86). El mínimo de 8 pedidos (S-06) solo cubre paradas de hasta S/ 40.
- Se anotaron cuatro huecos para el equipo en la spec.
- Resultado: 140 pruebas en verde (`docs/evidencia/desarrollo/08-metricas-verde.txt`).

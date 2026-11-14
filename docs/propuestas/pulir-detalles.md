# Pulir detalles: avisos de entregas y armado

Pedido de Aaron, 14/11/2026. Rama: `pulir-detalles`.

## Cambios previstos

1. Al liquidar con zonas pendientes, indicar «Entrega pendiente de registrar en: …» y conservar la lista de zonas. Registrar la entrega o su incidencia permite continuar; no se exige una confirmación individual de cada vecino.
2. Al agregar una bolsa antes del cierre, explicar que la semana todavía recibe compras y que el armado empieza el miércoles a las 8 p. m., hora de Lima.
3. Al registrar un producto dañado antes del cierre, explicar la misma condición con una acción específica para dañados.
4. Mostrar en Armado una ayuda permanente sobre el horario y aclarar en Liquidar qué registro falta, incluso antes de intentar la acción.

## Condiciones que se conservan

Los códigos `ZONES_PENDING` y `CYCLE_STILL_OPEN`, el cierre semanal y los permisos se conservan. Una zona fallida registrada también habilita la liquidación. Este cambio no crea un bloqueo por pagos pendientes ni modifica compras, saldos, fotos o bases de datos.

## Comprobaciones

- Antes del cierre, bolsa y dañado devuelven el código anterior y explican la causa, sin guardar cambios.
- A las 20:00 del miércoles ya se puede registrar una bolsa; se conserva la evidencia fotográfica.
- Las zonas pendientes se listan de forma estable; las ya entregadas no aparecen y las fallidas permiten continuar.
- Regresión del motor, frontend, TypeScript y build. Resultados en `pulir-detalles-validacion.md`.

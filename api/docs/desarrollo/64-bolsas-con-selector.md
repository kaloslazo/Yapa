# Iteración 64 · Seleccionar bolsas y confirmar sus fotos

## Requisito (Aaron, 13/11/2026)

En Armado, mostrar «Agregar bolsa · − 1 +» y un botón pequeño de confirmación a la derecha. El usuario confirmó que cada bolsa necesita una foto diferente.

## Alcance

- S-327 (a validar por el equipo): el selector indica bolsas nuevas pendientes de registrar, con mínimo 1. No disminuye bolsas ya guardadas. Se mantiene una foto por bolsa y la numeración del servidor.
- S-328 (a validar por el equipo): se envía cada foto por la API existente. Si falla una, se detiene el envío y se conservan solo las pendientes; las guardadas no se vuelven a enviar. Durante el envío se bloquea la edición.
- Se conservan los permisos y errores existentes: `CYCLE_STILL_OPEN`, `PHOTO_REQUIRED`, `ORDER_NOT_ATTENDED` y `ZONE_ALREADY_CLOSED`.

## Aceptación

1. Al inicio hay 1 campo de foto; «+» muestra 2, «−» vuelve a 1 y nunca baja de 1.
2. Con 2 bolsas se requieren 2 fotos. Se envían en orden y, al completar, vuelve a 1 campo vacío.
3. Si se guarda la primera y falla la segunda, queda pendiente solo la segunda foto; reintentar no duplica la primera.
4. El selector y confirmar tienen nombres accesibles, soportan teclado y se bloquean durante el envío.
5. Cambiar de semana o pedido reinicia el borrador; Compras, Reparto y los otros formularios de fotos mantienen su comportamiento.

## Validación prevista

Pruebas del formulario con éxito, fallo parcial y bloqueo; regresión frontend, TypeScript y build. La API no cambia.

# Iteración 71 · Una foto, revisión y bolsa

Pedido de Aaron, 17/11/2026. Base 8b24c0e. S-357..S-360, a validar por el equipo: una foto equivale a una bolsa; las unidades detectadas nunca se convierten en kilos; una papa se asigna automáticamente solo si existe una única variedad en el pedido; la baja de una bolsa se permite antes del despacho y conserva su foto y un registro de auditoría.

AR71-1: una sola cámara analiza de forma predeterminada y lista todos los grupos detectados. Se eliminan las rutas de interfaz duplicadas. Si falla el detector, permite completar manualmente. No guarda sin confirmación.
AR71-2: cada fila elige un SKU del pedido, permite corregir unidades y tiene un check. Al confirmar la fila se marca la lista superior como comprobación visual, no como peso completo. Si hay ambas papas se exige elegir cuál. Solo se guardan filas confirmadas y se conserva la revisión con la bolsa.
AR71-3: se pueden guardar otras fotos como otras bolsas. No se reenvía una bolsa ya confirmada al editar la misma revisión.
AR71-4: quitar una bolsa exige confirmación y permisos, no elimina archivos de fotos, no renumera sus identificadores y deja constancia. Se bloquea con ZONE_ALREADY_CLOSED si salió a reparto, fue entregada/fallida o liquidada. Inexistente: BAG_NOT_FOUND. Revisión inválida: INVALID_BAG_REVIEW.

Aceptación: papa única asignada, papa ambigua sin asignar, corrección/manual, persistencia y baja con identificadores estables; antes del cierre conserva CYCLE_STILL_OPEN. No se alteran cantidades, pagos, faltantes ni catálogo.


## Trazabilidad y validación local

- AR71-1/2: PhotoProductReview, photoMatches y PackCard; photoMatches.test y caso de papa ambigua en PhotoProductReview.test. La prueba de cámara ahora exige análisis previo y ausencia de guardado automático.
- AR71-3/4: fulfillment.pack_bag/remove_bag, bag_reviews/bag_counters/bag_removals, endpoints de bolsa y baja; test_armado71 y regresión de fotos/persistencia. La foto no se borra.
- 768 pruebas del motor ejecutadas: 764 aprobadas y 4 omitidas. 213 pruebas web aprobadas; TypeScript y build aprobados. Evidencia 71-armado-*-verde.txt. Permanece el aviso Vite por chunk mayor de 500 kB y un ResourceWarning SQLite de la suite.
- Siguiente validación conjunta: recorrido en navegador de las cuatro vistas sobre esta base. No se alteró dinero, inventario publicado ni infraestructura.

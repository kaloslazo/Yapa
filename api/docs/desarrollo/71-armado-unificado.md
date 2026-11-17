# Iteración 71 · Una foto, revisión y bolsa

Pedido de Aaron, 17/11/2026. Base 8b24c0e. S-357..S-360, a validar por el equipo: una foto equivale a una bolsa; las unidades detectadas nunca se convierten en kilos; una papa se asigna automáticamente solo si existe una única variedad en el pedido; la baja de una bolsa se permite antes del despacho y conserva su foto y un registro de auditoría.

AR71-1: una sola cámara analiza de forma predeterminada y lista todos los grupos detectados. Se eliminan las rutas de interfaz duplicadas. Si falla el detector, permite completar manualmente. No guarda sin confirmación.
AR71-2: cada fila elige un SKU del pedido, permite corregir unidades y tiene un check. Al confirmar la fila se marca la lista superior como comprobación visual, no como peso completo. Si hay ambas papas se exige elegir cuál. Solo se guardan filas confirmadas y se conserva la revisión con la bolsa.
AR71-3: se pueden guardar otras fotos como otras bolsas. No se reenvía una bolsa ya confirmada al editar la misma revisión.
AR71-4: quitar una bolsa exige confirmación y permisos, no elimina archivos de fotos, no renumera sus identificadores y deja constancia. Se bloquea con ZONE_ALREADY_CLOSED si salió a reparto, fue entregada/fallida o liquidada. Inexistente: BAG_NOT_FOUND. Revisión inválida: INVALID_BAG_REVIEW.

Aceptación: papa única asignada, papa ambigua sin asignar, corrección/manual, persistencia y baja con identificadores estables; antes del cierre conserva CYCLE_STILL_OPEN. No se alteran cantidades, pagos, faltantes ni catálogo.

# Iteración 72 · Stock confirmado por cargas

S-361..S-364 (a validar por el equipo): inventario confirmado separado por proveedor y semana de propuesta; comienza en cero y acumula solo cargas revisadas. La misma foto exacta no se suma dos veces en esa semana. Para kg se exige peso medido, nunca se convierte el número de objetos. El máximo vendible se redondea hacia abajo al paso del catálogo. La disponibilidad del borrador se reemplaza por el total vendible confirmado; publicar sigue exigiendo envío y aprobación existentes.

ST72-1: una foto admite múltiples verduras y múltiples filas del mismo SKU; se suman por producto. Se elige SKU exacto cuando la clase es ambigua. La confirmación persiste unidades, peso/cantidad y huella de la foto; recargar recupera el stock.
ST72-2: repetir foto/conteo devuelve el mismo total sin sumar. Foto repetida con otro conteo: STOCK_ALREADY_CONFIRMED. Aislamiento por proveedor y semana. No guarda fotos de análisis ni modifica reservas, precios o catálogo publicado.
ST72-3: solo productos del proveedor, unidades enteras 1..300, peso positivo y finito para kg, ciclo de la próxima semana. Errores INVALID_STOCK_ITEM, WEIGHT_REQUIRED, INVALID_STOCK_CYCLE; permisos NOT_AUTHORIZED.
ST72-4: cada producto tiene precios por volumen en un desplegable propio, cerrado al inicio. Se conserva el lector de cotizaciones de Kalos. Stock y propuesta no se publican solos; enviar la lista sigue usando el endpoint anterior. Fotos distintas de una misma carga física no se pueden deduplicar con esta primera versión: el proveedor debe evitar registrarla dos veces.

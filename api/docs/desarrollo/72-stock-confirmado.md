# Iteración 72 · Stock confirmado por cargas

S-361..S-364 (a validar por el equipo): inventario confirmado separado por proveedor y semana de propuesta; comienza en cero y acumula solo cargas revisadas. La misma foto exacta no se suma dos veces en esa semana. Para kg se exige peso medido, nunca se convierte el número de objetos. El máximo vendible se redondea hacia abajo al paso del catálogo. La disponibilidad del borrador se reemplaza por el total vendible confirmado; publicar sigue exigiendo envío y aprobación existentes.

ST72-1: una foto admite múltiples verduras y múltiples filas del mismo SKU; se suman por producto. Se elige SKU exacto cuando la clase es ambigua. La confirmación persiste unidades, peso/cantidad y huella de la foto; recargar recupera el stock.
ST72-2: repetir foto/conteo devuelve el mismo total sin sumar. Foto repetida con otro conteo: STOCK_ALREADY_CONFIRMED. Aislamiento por proveedor y semana. No guarda fotos de análisis ni modifica reservas, precios o catálogo publicado.
ST72-3: solo productos del proveedor, unidades enteras 1..300, peso positivo y finito para kg, ciclo de la próxima semana. Errores INVALID_STOCK_ITEM, WEIGHT_REQUIRED, INVALID_STOCK_CYCLE; permisos NOT_AUTHORIZED.
ST72-4: cada producto tiene precios por volumen en un desplegable propio, cerrado al inicio. Se conserva el lector de cotizaciones de Kalos. Stock y propuesta no se publican solos; enviar la lista sigue usando el endpoint anterior. Fotos distintas de una misma carga física no se pueden deduplicar con esta primera versión: el proveedor debe evitar registrarla dos veces.

## Trazabilidad y validación

- ST72-1/2: supplier_stock.confirm/snapshot, supplier_stock_batches en Store y persistencia existente; test_stock72 cubre acumulación, repetición, aislamiento y reapertura de SQLite.
- ST72-3: autorización de los endpoints de stock, validación atómica de SKU/unidades/peso y ciclo; no modifica el catálogo. SupplierListEditor solo aplica totales a filas con la misma unidad, y avisa si difieren.
- ST72-4: SupplierStock, SupplierListEditor y stock72.test. Desplegable independiente de precios; QuoteReader conservado. PhotoProductReview permite volver a seleccionar la misma foto y el servidor evita volver a sumar esa carga.
- 774 pruebas del motor: 770 aprobadas y 4 omitidas; 216 web, TypeScript y build aprobados. Evidencias 72-stock-*-verde.txt. Las correcciones finales se comprobaron con las suites de foto, stock y cámara, TypeScript y build.
- Chrome móvil con fotos y YOLO reales: dos cargas del mismo SKU acumulan 5 unidades visibles y 4 kg medidos; repetir una no suma; recarga conserva el total y el borrador de 4 kg. Capturas actuales en docs/modelo-yolo.
- Límite explícito: no reconoce cargas físicas fotografiadas de nuevo; no convierte unidades a peso ni publica automáticamente. No se tocaron AWS ni bases locales anteriores.

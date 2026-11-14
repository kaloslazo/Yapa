# Revisión de productos por foto

YOLOv8 Small, entrenado con Vegetable 4: papa, cebolla, ajo y zanahoria. Se integra el best.pt del ZIP de entrenamiento; yolov8s (2).pt descargado es el modelo COCO base de 80 clases.

Armado y Proveedor pueden analizar una foto, revisar cantidades de objetos visibles, cambiar producto y cantidad, agregar o quitar filas y confirmar. El análisis es opcional, no publica productos ni modifica pedidos, pesos o precios. En Armado, confirmar permite guardar esa misma foto como una bolsa mediante el endpoint existente y respetando el cierre semanal. En Proveedor se confirma una referencia en pantalla; su lista semanal se sigue editando y enviando por separado. El conteo revisado vive en memoria, no se añade a la base ni sustituye la evidencia de la bolsa.

El conteo se obtiene sumando cajas detectadas, sin herramientas adicionales al detector. No estima kilos, contenido oculto, limón, camote ni variedades de papa. Si falla la inferencia, se puede introducir la revisión manualmente y se conservan los controles habituales. La foto del análisis no se guarda en el servidor. API con sesión y CSRF, solo admin, armador y proveedor.

Validación: API, permisos y errores; revisión editable y solicitudes antiguas; prueba real de inferencia con el modelo, y regresión completa. Resultados y gráficos en README de esta rama.

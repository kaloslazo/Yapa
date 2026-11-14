# Ruta local de reparto

Sin servicios nuevos ni claves: minimapa SVG esquemático basado en las coordenadas ya registradas y algoritmo de vecino cercano con mejora de segmentos (2-opt). Compara la propuesta con el orden inicial y conserva el de menor distancia en línea recta. No calcula calles, tráfico, semáforos ni garantiza el óptimo global.

El usuario elige una zona pendiente como inicio y puede aplicar o quitar la sugerencia. Una parada en camino se conserva al inicio; las completadas se muestran al final. Las zonas sin coordenadas siguen en la lista y se avisa que quedan fuera del cálculo. Una zona agrupa sus pedidos en una sola parada. No cambia permisos, entregas ni avisos y no guarda ubicaciones GPS. Aceptación: mejora o conserva la distancia, no omite pedidos ni zonas, excluye completadas del cálculo y funciona sin peticiones de mapas o geolocalización.

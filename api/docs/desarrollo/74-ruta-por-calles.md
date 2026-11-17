# Iteración 74 · Recorrido por calles sobre el mapa de Kalos

S-366 (a validar por el equipo): conservar el mapa Leaflet/OpenStreetMap y el enlace Google Maps de main. Añadir cálculo explícito del recorrido por calles del orden elegido mediante OSRM, sin LLM ni nuevas bibliotecas. El servidor usa YAPA_ROUTING_URL, por defecto https://router.project-osrm.org, solo para demostración académica moderada; en producción se debe elegir un servicio apropiado o alojar el motor. No se promete tráfico, semáforos ni un orden global óptimo por carretera.

RP74-1: botón «Trazar por calles» para 2..25 zonas pendientes; API deriva coordenadas de las zonas atendidas autorizadas del ciclo. No acepta destinos arbitrarios. Roles admin/transportista y CSRF existentes.
RP74-2: geometría real dibujada como línea continua, distancia vial y tiempo estimado sin tráfico en tiempo real. El orden sugerido sigue siendo la heurística geográfica y se identifica como tal.
RP74-3: petición externa con timeout, respuesta acotada, caché 10 minutos y límite global de una solicitud por segundo. Caída, timeout, coordenadas inválidas o respuesta mal formada: ROUTE_UNAVAILABLE / INVALID_ROUTE / ROUTE_BUSY. No se dibuja una recta como si fuera una calle.
RP74-4: cambiar el inicio invalida el trazado anterior. La UI ignora respuestas antiguas. No cambia salidas, entregas, permisos o infraestructura AWS. Rehacer el mapa de Kalos está en pausa; esta extensión aprovecha su componente.

## Trazabilidad y validación

- RP74-1/3: street_routing y endpoint /api/reparto/ruta; test_route74 cubre caché, permisos, coordenadas de zonas autorizadas, timeout y geometría inválida. La API externa se simula en la suite.
- RP74-2/4: RoutePlanner, LazyRouteMap y RouteMap; route74.test y regresión RoutePlanner.test. Se conservan Leaflet, Google Maps y la heurística, con métricas diferenciadas y descarte de respuestas antiguas. Los nombres de las paradas se insertan como texto en el tooltip.
- 768 pruebas motor (764 aprobadas y 4 omitidas), 213 web, TypeScript y build aprobados: 74-ruta-*-verde.txt.
- Chrome con OSRM real: HTTP 200, 92 puntos de geometría, 2,63 km para tres zonas; cambiar el inicio invalida el trazado. Captura a 390 px en docs/ruta-local/reparto-17nov.png.

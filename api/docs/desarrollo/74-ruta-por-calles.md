# Iteración 74 · Recorrido por calles sobre el mapa de Kalos

S-366 (a validar por el equipo): conservar el mapa Leaflet/OpenStreetMap y el enlace Google Maps de main. Añadir cálculo explícito del recorrido por calles del orden elegido mediante OSRM, sin LLM ni nuevas bibliotecas. El servidor usa YAPA_ROUTING_URL, por defecto https://router.project-osrm.org, solo para demostración académica moderada; en producción se debe elegir un servicio apropiado o alojar el motor. No se promete tráfico, semáforos ni un orden global óptimo por carretera.

RP74-1: botón «Trazar por calles» para 2..25 zonas pendientes; API deriva coordenadas de las zonas atendidas autorizadas del ciclo. No acepta destinos arbitrarios. Roles admin/transportista y CSRF existentes.
RP74-2: geometría real dibujada como línea continua, distancia vial y tiempo estimado sin tráfico en tiempo real. El orden sugerido sigue siendo la heurística geográfica y se identifica como tal.
RP74-3: petición externa con timeout, respuesta acotada, caché 10 minutos y límite global de una solicitud por segundo. Caída, timeout, coordenadas inválidas o respuesta mal formada: ROUTE_UNAVAILABLE / INVALID_ROUTE / ROUTE_BUSY. No se dibuja una recta como si fuera una calle.
RP74-4: cambiar el inicio invalida el trazado anterior. La UI ignora respuestas antiguas. No cambia salidas, entregas, permisos o infraestructura AWS. Rehacer el mapa de Kalos está en pausa; esta extensión aprovecha su componente.

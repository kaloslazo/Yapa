# Iteración 74 · Recorrido por calles para el reparto

> **Reescrita el 18/11/2026** con el formato de las demás specs. Las reglas y las pruebas son las mismas; el código del motor se pasó al estilo del repo sin cambiar lo que hace.

## Requisito (Aaron, 17/11/2026)

Como transportista, quiero ver en el mapa el camino real por calles del orden de paradas que elegí, con distancia y tiempo, para saber cuánto me toma la ruta.

## Alcance

Se conservan el mapa de OpenStreetMap, el orden sugerido en línea recta y el botón de Google Maps. El recorrido por calles se pide con un botón; no cambia el orden, las salidas ni las entregas. No usa IA.

## Supuestos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-366 | El recorrido lo calcula un servicio compatible con OSRM (`YAPA_ROUTING_URL`). Por defecto es el servidor público de demostración `router.project-osrm.org`, que sirve para el curso pero no para producción: para operar de verdad hay que elegir otro servicio o alojar uno. El tiempo es sin tráfico. | caché 10 min, 1 consulta por segundo |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| RP74-1 | `POST /api/reparto/ruta` con `ciclo` y `zonas` (lista JSON de 2 a 25 zonas distintas). Las coordenadas salen de las zonas atendidas y pendientes de esa semana; el navegador no puede mandar puntos propios. Solo admin y transportista. | `INVALID_ROUTE`, 401 / 403 |
| RP74-2 | Devuelve la línea por calles, la distancia en metros y el tiempo en segundos. La pantalla la dibuja como línea continua y la distingue de la recta. | — |
| RP74-3 | Si el servicio no responde en 7 s, responde mal o con una línea inválida, no se dibuja nada parecido a una calle. La misma ruta se guarda 10 minutos; entre dos consultas al servicio pasa al menos 1 segundo. | `ROUTE_UNAVAILABLE`, `ROUTE_BUSY` |
| RP74-4 | Cambiar el inicio o la semana borra el recorrido anterior y descarta respuestas viejas. | — |

## Criterios de aceptación

- **RP74-A · Recorrido y caché.** Con dos paradas, el servicio responde 1200 m y la línea; la segunda vez sale de la caché sin llamar al servicio. → RP74-2, RP74-3
- **RP74-B · Parada inválida o servicio caído.** Una parada en (999, 0) da `INVALID_ROUTE`; si el servicio no responde, `ROUTE_UNAVAILABLE`. → RP74-1, RP74-3
- **RP74-C · Línea rota.** Una línea con `NaN` da `ROUTE_UNAVAILABLE`. → RP74-3
- **RP74-D · API.** Con 8 pedidos en Z-JM-01 y 8 en Z-LINCE-01, el admin pide la ruta y al servicio le llegan las coordenadas de esas dos zonas; con una zona `DESCONOCIDA`, `INVALID_ROUTE`; sin sesión, 401. → RP74-1
- **RP74-E · Pantalla.** No se pide nada hasta tocar "Trazar por calles"; con 2500 m dice "Recorrido vial: 2.50 km" y el mapa recibe los 2 puntos. → RP74-2
- **RP74-F · Falla en pantalla.** Si falla, se ve el error y el mapa no recibe puntos de calle. → RP74-3

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| RP74-1 | `web/api.py` `reparto_ruta` | `test_route74.test_rp74_b_*`, `test_rp74_d_*` |
| RP74-2, RP74-3, S-366 | `street_routing.py` (`street_route`, `_ask_service`, caché y espera de 1 s) | `test_rp74_a_*`, `test_rp74_b_*`, `test_rp74_c_*` |
| RP74-2, RP74-4 | `RoutePlanner.tsx` (`trace`, `requestVersion`), `RouteMap.tsx`, `LazyRouteMap.tsx` | `route74.test.ts` (RP74-E, RP74-F), `RoutePlanner.test.ts` |

## Evidencia

`74-ruta-rojo.txt`, `74-ruta-motor-verde.txt` y `74-ruta-web-verde.txt` (17/11/2026, en la máquina de Aaron).

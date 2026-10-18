# Iteración 38 · Mapa real de zonas, sección Zonas del admin y unión visible

## Requisito

Como admin de Yapa, quiero ver todas las zonas sobre un mapa real con su perímetro, qué zonas están unidas y cuáles se pueden unir hoy, y leer las propuestas del sistema. Como admin de zona, quiero ver mi zona y las cercanas sobre un mapa real y entender por qué una unión se puede o no.

## Por qué

Pedido del equipo (18/10/2026): ver las zonas por perímetros en un mapa real y ver cómo se fusionan cuando los dos admins están de acuerdo y el sistema lo permite. El mapa de Mi zona era un dibujo esquemático sin calles; el admin de Yapa no tenía ningún mapa. El motor ya sabe unir (iteración 5) y desde la iteración 37 dice qué uniones convienen.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-190 | **Mapa real.** Se usa la librería Leaflet con los mosaicos públicos de OpenStreetMap (con su atribución). Es para el piloto: antes de lanzar con mucho tráfico hay que pasar a un proveedor de mosaicos propio o de pago. Los mosaicos se piden desde el navegador a un servicio externo. | OpenStreetMap |
| S-191 | **Perímetro de una zona.** Un círculo de 300 m alrededor del punto de recepción (el radio al que se puede vivir para unirse, S-25). La unión se muestra con un anillo de 500 m (S-26). Es una guía visual, no un polígono dibujado a mano. | 300 m y 500 m |
| S-192 | **Colores por grupo.** Las zonas de un mismo grupo (ya unidas) comparten color. | — |
| S-193 | La sección **Zonas** del admin de Yapa solo mira y propone: no une ni separa zonas. La unión la piden y aceptan los admins de zona. | — |

## Reglas

| Regla | Comportamiento |
|---|---|
| MP-01 | El mapa dibuja cada zona con ubicación como un círculo de 300 m del color de su grupo, con su nombre. Las zonas sin ubicación no se dibujan y se avisa cuántas faltan. |
| MP-02 | Las zonas de grupos distintos a 500 m o menos se unen con una línea y su distancia: verde continua si se pueden unir hoy, gris punteada si algo lo impide, con el motivo en palabras. |
| MP-03 | El mapa se encuadra primero en las zonas que están unidas o que se pueden unir (si no hay ninguna, en todas) para que los nombres no se pisen; el botón "Ver todas las zonas" las muestra todas. Con una sola zona se acerca a ella. |
| MP-04 | El mapa se puede usar con teclado y tiene nombre para lectores de pantalla; la información importante (zonas, distancias, motivos) también está en una lista debajo, no solo en el dibujo. |
| MP-05 | Si no cargan los mosaicos (sin internet), los círculos y la lista siguen visibles sobre un fondo liso. |
| MP-06 | Motivos en palabras: ciclo cerrado → "Solo se unen zonas con el ciclo abierto"; muy lejos → "Están muy lejos para compartir camión"; sin ubicación → "Falta registrar la ubicación de una zona". |
| MP-07 | Sección **Zonas** en el menú del admin: mapa con todas las zonas, propuestas del sistema (con su tipo y los datos que la originan) y tabla por zona con vecinos, pedidos, verificados, adopción y margen. Con el margen sin liquidar dice "Sin liquidar". |
| MP-08 | El menú muestra el número de propuestas junto a **Zonas**. |
| MP-09 | En Mi zona (admin de zona) el mapa esquemático se reemplaza por el mapa real con su zona resaltada y las cercanas; la lista de "Pedir unión" y las solicitudes siguen igual. |
| MP-10 | En Mi zona, cada zona cercana sin unir dice si hoy se puede pedir la unión; si no, el motivo en palabras. |
| MP-11 | En Mi zona, una unión ya pedida muestra "Esperando a su admin" con la opción de retirarla; cuando el otro admin acepta, las dos zonas pasan a "Unidas". |
| MP-12 | Los conteos de vecinos usan singular y plural correctos. |

## Criterios de aceptación (`src/utils/zoneMap.test.ts`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| MP-A | Mismo grupo, mismo color | dos zonas del grupo "G-LINCE" | el mismo color |
| MP-B | Grupos distintos, colores distintos | "G-LINCE", "G-JM", "G-LV" | tres colores distintos |
| MP-C | El color no cambia al agregar un grupo | calcular con 2 y con 3 grupos | los 2 primeros conservan su color |
| MP-D | Zonas sin ubicación | 3 zonas, una con `lat: null` | 2 zonas dibujables |
| MP-E | Motivo en palabras | `CYCLE_CLOSED`, `ZONES_TOO_FAR`, `LOCATION_REQUIRED` | los textos de MP-06 |
| MP-F | Motivo desconocido | `OTRO` | un texto general, nunca el código |
| MP-G | Etiqueta de unión posible | 391 m, sin motivo | "391 m · se puede unir hoy" |
| MP-H | Etiqueta de unión bloqueada | 455 m, `ZONES_TOO_FAR` | "455 m · Están muy lejos para compartir camión" |
| MP-I | Margen sin liquidar | `null` | "Sin liquidar" |
| MP-J | Margen negativo | "-12.50" | "-S/ 12.50" |
| MP-N | Singular y plural | 1, 0 y 8 vecinos | "1 vecino", "0 vecinos", "8 vecinos" |
| MP-K | Zonas en foco | 3 zonas: dos del mismo grupo, una suelta lejos, sin uniones | solo las dos del mismo grupo |
| MP-L | Zonas en foco con unión | una suelta con unión a otra zona | las dos zonas de la unión |
| MP-M | Sin nada que enfocar | 3 zonas sueltas sin uniones | las 3 |

Las reglas de pantalla (MP-01..MP-05, MP-07..MP-10) se verifican en el navegador a escritorio y a 390 px.

## Trazabilidad

Se completa al terminar la implementación.

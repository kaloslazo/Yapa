# Contexto de negocio

## Yapa

Yapa es una startup ficticia para el curso Diseño de Software. Su propuesta es consolidar compras mayoristas de vecinos de Lince, Jesús María y La Victoria. Los clientes arman su canasta durante la semana, el ciclo cierra el miércoles a las 20:00 y el negocio coordina compra, preparación y reparto para el sábado.

## Problema

El supermercado ofrece cercanía pero suele ser más caro. El mercado mayorista ofrece mejores precios, pero exige tiempo, traslado y carga. Yapa reparte el costo del viaje entre pedidos de una misma zona.

## Actores externos

- `AN-01 Cliente`: consulta catálogo, registra pedido, elige entrega, paga, recibe y reporta incidencias.
- `AN-02 Proveedor mayorista`: cotiza y abastece.
- `AN-03 Entidad financiera o billetera digital`: procesa transferencias y referencias.
- `AN-04 Servicio de mapas y geocodificación`: valida coordenadas y estima rutas.

## Trabajadores internos

Administrador, encargado de compras, preparador de pedidos, repartidor y personal de atención al cliente.

## Casos de uso del negocio

`CUN-01 Actualizar catálogo y precios`, `CUN-02 Registrar pedido semanal`, `CUN-03 Procesar pago`, `CUN-04 Consolidar pedidos por zona`, `CUN-05 Abastecer compra consolidada`, `CUN-06 Preparar pedidos`, `CUN-07 Planificar y ejecutar entrega` y `CUN-08 Resolver incidencia`.

## Fuente

Este contexto resume el `Entregable01_ModeladoNegocio_Yapa.pdf`. El repositorio general contiene el mapa completo; este repositorio solo implementa CUN-02 y el límite mínimo de CUN-03.


## Cambios del modelo en la iteración 2

Después de revisar los antecedentes (Favo, Muni, Merqueo) y los precios reales, el equipo ajustó el modelo (detalle en `10-clarificaciones-v2.md`):

- **La zona es un punto de recepción** (portería o encargado) creado por un vecino admin. El camión hace una sola parada por zona.
- **Se paga por adelantado** con Yape o Plin el precio máximo. No hay contraentrega.
- **"Te devolvemos"**: después de la entrega, el ahorro por volumen, el envío compartido y los faltantes vuelven como saldo a favor.
- **Catálogo piloto**: frescos resistentes y limpieza de marcas emergentes, que es donde hay margen real.

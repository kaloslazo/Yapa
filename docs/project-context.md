# Contexto funcional de Yapa

## Problema y propuesta

Yapa es una plataforma web para consolidar compras mayoristas por zona. Busca que hogares y pequeños compradores accedan a mejores precios sin tener que coordinar directamente una compra mayorista completa.

El piloto considera los distritos de Lince, Jesús María y La Victoria. La operación se organiza por ciclos semanales: se reciben pedidos hasta el miércoles por la noche, se consolida la demanda, se compra al proveedor, se preparan los pedidos y se entrega el sábado.

## Ciclo operativo

1. El cliente consulta el catálogo vigente.
2. El cliente registra un pedido dentro del ciclo semanal.
3. El pedido se paga o queda con un medio de pago permitido.
4. Yapa consolida pedidos por zona y ventana de entrega.
5. Yapa repone la compra consolidada al proveedor mayorista.
6. El equipo prepara los pedidos.
7. Se planifican y ejecutan las entregas.
8. Se resuelven faltantes, daños, rechazos e incidencias.

## Actores externos

- Cliente.
- Proveedor mayorista.
- Entidad financiera o billetera digital.
- Servicio de mapas y geocodificación.

## Roles internos

- Administrador.
- Responsable de compras.
- Preparador de pedidos.
- Repartidor.
- Atención al cliente.

## Casos de uso del negocio

| Código | Caso de uso |
|---|---|
| CUN-01 | Actualizar catálogo y precios |
| CUN-02 | Registrar pedido semanal |
| CUN-03 | Procesar pago |
| CUN-04 | Consolidar por zona |
| CUN-05 | Reponer compra consolidada |
| CUN-06 | Preparar pedidos |
| CUN-07 | Planificar y ejecutar entrega |
| CUN-08 | Resolver incidencia |

## Entidades principales

Cliente, Dirección, Zona, Ciclo semanal, Producto, Cotización, Pedido, Detalle de pedido, Pago, Ruta, Parada de entrega e Incidencia.

## Reglas de negocio

- **RN-01:** solo se atienden los distritos piloto.
- **RN-02:** el ciclo recibe pedidos desde el lunes 00:00 hasta el miércoles 20:00.
- **RN-03:** el subtotal mínimo del pedido es S/ 50.00.
- **RN-04:** el delivery cuesta S/ 7.90 y se exonera desde un subtotal de S/ 120.00.
- **RN-05:** todo precio tiene unidad de venta y vigencia.
- **RN-06:** el peso variable admite como máximo una variación de 5%.
- **RN-07:** el pedido requiere al menos un producto activo, dirección válida y ventana disponible.
- **RN-08:** ante una sustitución, el cliente acepta el cambio o recibe devolución.
- **RN-09:** las ventanas del sábado son 09:00–12:00, 12:00–15:00 y 15:00–18:00, con capacidad.
- **RN-10:** se permiten transferencia, billetera digital y contraentrega.
- **RN-11:** la transferencia debe verificarse hasta el jueves 12:00.
- **RN-12:** una referencia de transferencia no puede conciliar múltiples pedidos.
- **RN-13:** solo pedidos consolidados pueden comprarse y prepararse.
- **RN-14:** la consolidación excluye cancelados y conserva zona y ventana.
- **RN-15:** productos perecibles dañados o no aceptables se excluyen del pedido.
- **RN-16:** solo el administrador publica precios y vigencias.
- **RN-17:** una ruta sugerida por IA requiere aprobación del administrador.
- **RN-18:** ante una entrega fallida se hacen dos intentos de contacto y se espera como máximo diez minutos.
- **RN-19:** faltantes o daños se reportan dentro de 24 horas.
- **RN-20:** se puede cancelar sin penalidad hasta el cierre del miércoles; luego solo por faltante, daño o error de Yapa.
- **RN-21:** se cobra el precio de referencia y se ajusta el peso real al entregar; Yapa asume temporalmente la diferencia.
- **RN-22:** si el cliente rechaza pagar, no se entrega, se registra incidencia y se suspende al cliente.

## Límites conocidos

El modelado de negocio no demuestra todavía viabilidad comercial completa, integración real con proveedores, pagos, mapas, logística ni operación productiva. Las sugerencias automáticas, especialmente de rutas, deben quedar bajo aprobación humana.

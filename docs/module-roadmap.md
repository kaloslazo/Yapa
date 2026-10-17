# Roadmap de módulos

| Orden | Módulo | Dependencias principales | Próximo entregable |
|---:|---|---|---|
| 1 | CUN-01 Catálogo y precios | Producto, Cotización, permisos de administrador | catálogo vigente por unidad y fecha |
| 2 | CUN-02 Pedido semanal | Cliente, Dirección, Zona, Ciclo, Producto | pedido válido por ciclo y ventana |
| 3 | CUN-03 Pago | Pedido, Pago, conciliación | pago permitido y estado verificable |
| 4 | CUN-04 Consolidación | Pedido, Zona, ventana | demanda consolidada sin cancelados |
| 5 | CUN-05 Compra mayorista | Consolidación, proveedor, peso variable | compra preparada para abastecimiento |
| 6 | CUN-06 Preparación | Compra, Pedido, sustituciones | pedido listo o incidencia |
| 7 | CUN-07 Entrega | Ruta, Parada, mapas, capacidad | ruta aprobada y entrega registrada |
| 8 | CUN-08 Incidencias | Pedido, entrega, cliente | resolución, devolución o suspensión |

## Orden recomendado

El repositorio SDD de la exposición implementa una vertical pequeña de CUN-02 y cubre el contrato mínimo del medio de pago de CUN-03. El proyecto completo debe continuar con:

1. catálogo y precios vigentes;
2. persistencia de clientes, direcciones, ciclos y pedidos;
3. conciliación de pagos;
4. consolidación y compra;
5. preparación, rutas, entrega e incidencias.

Cada incremento debe conservar trazabilidad con el caso de uso, las reglas afectadas, los criterios de aceptación y la evidencia de validación.

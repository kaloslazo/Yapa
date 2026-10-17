# Decisiones iniciales de diseño

## Ciclo semanal con cierre explícito

El ciclo cierra el miércoles a las 20:00. Esto permite separar registro de pedidos, consolidación, compra, preparación y entrega. No se debe aceptar una orden tardía como si perteneciera al ciclo anterior.

## Precio de referencia y peso real

El pedido usa un precio de referencia vigente para poder registrar la compra. En la entrega se ajusta el peso real cuando corresponda; Yapa asume temporalmente la diferencia para no trasladar una incertidumbre operacional al cliente durante el registro.

## Pago como estado, no como simple booleano

Un pedido puede registrar el medio de pago y luego pasar por estados de verificación o conciliación. La referencia de transferencia debe ser única por pedido conciliado.

## Ruteo con aprobación humana

La IA o el motor de mapas puede sugerir una ruta, pero el administrador debe aprobarla antes de convertirla en una instrucción operativa. La sugerencia no reemplaza la responsabilidad del equipo.

## Alcance incremental

La primera entrega de SDD no pretende resolver todo Yapa. CUN-02 es una vertical demostrable; consolidación, abastecimiento, preparación, entrega e incidencias quedan explícitamente en roadmap.

## Decisiones pendientes

- proveedor y contrato de catálogo;
- pasarela o billeteras concretas;
- estrategia de persistencia y auditoría;
- cálculo de capacidad por zona y ventana;
- políticas de sustitución y devolución;
- métricas operativas y de satisfacción.

## Primera implementación web local

La primera superficie ejecutable del repositorio general es una app web local con
React, TypeScript y Vite. Incluye catálogo, canasta, autenticación, dirección de
entrega con mapa simulado, registro de pedidos, historial y panel admin. La capa de
persistencia usa Supabase cuando existen variables de entorno y conserva un modo
local explícito para validar el flujo sin infraestructura.

React se usa para separar la superficie en componentes y mantener el estado de la
canasta y del checkout de forma explícita. Vite queda como herramienta de desarrollo,
build y preview; no se considera el framework de UI.

La dirección visual usa Fraunces para titulares y DM Sans para la interfaz. Los
productos del catálogo usan recortes PNG RGBA generados específicamente para Yapa,
sin logos ni texto incrustado, para mantener una presentación editorial consistente
sin depender de imágenes remotas.

El incremento actual cubre la lectura del catálogo, filtros, cálculo de subtotal,
delivery y total estimado, además de la creación de pedidos con sus detalles. En
modo Supabase, RLS separa los datos del cliente y del administrador, y una función
RPC registra pedido, dirección y detalles de forma atómica. Los pagos siguen
simulados y la dirección solo se transmite al proyecto Supabase configurado por el
equipo. `supabase/schema.sql` contiene el esquema ejecutable y sus políticas.

# Plan técnico · iteración 2

## Decisión

Se mantiene Python 3.11 sin dependencias externas (decisión del equipo) y se separa en capas para que cada regla tenga un solo lugar:

| Módulo | Responsabilidad | Reglas |
|---|---|---|
| `domain.py` | Datos del negocio (producto con tramos, zona, cliente, pedido), constantes del piloto, error de negocio, redondeo a favor del cliente | S-04..S-09 |
| `cycle.py` | Hora de Lima, identificador del ciclo y si el ciclo está abierto | RP-03 |
| `store.py` | Repositorio en memoria: clientes, zonas, catálogo, pedidos, stock reservado y códigos de operación usados | RP-04, RP-08, RP-13 |
| `order_registration.py` | Registrar pedido y verificar pago (CUN-02 + límite CUN-03) | RP-01..RP-15 |
| `settlement.py` | Liquidar el ciclo | LQ-01..LQ-09 |
| `seed.py` | Catálogo piloto, zonas y clientes de ejemplo (S-12) | — |
| `cli.py` | Adaptador de consola para la demo en vivo | — |

**Por qué así:** las reglas no dependen de la consola ni del repositorio. Si mañana se cambia la CLI por una API web, o la memoria por PostgreSQL, `order_registration.py` y `settlement.py` no cambian.

## Qué no se decide todavía

Base de datos, framework web, autenticación e integración con Yape o Plin. Ver `10-clarificaciones-v2.md`.

## Diagramas

Ver `12-diseno.md`.

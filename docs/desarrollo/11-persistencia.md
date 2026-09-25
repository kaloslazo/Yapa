# Iteración 11 · Persistencia en SQLite

## Requisito

Como Yapa, quiero que los pedidos, saldos, zonas y reclamos **no se pierdan si el servidor se apaga o se reinicia**, porque el saldo es plata de los clientes (C-05) y la liquidación depende de todos los pedidos de la semana.

## Por qué así

Hasta la iteración 10, todo vivía en memoria (S-62). Las reglas de negocio modifican los objetos directamente: un pedido cambia de estado, un pago se reduce, etc. Reescribir cada caso de uso para que guarde fila por fila sería un cambio grande y riesgoso. Para el piloto, de decenas de pedidos por semana, alcanza con **guardar el estado completo después de cada operación que termina bien**, dentro de una transacción de SQLite (biblioteca estándar).

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-90 | Se guarda el estado completo después de cada operación de la web que termina bien. Alcanza para el volumen del piloto; con miles de pedidos habría que pasar a guardar por tabla. | — |
| S-91 | Las **sesiones no se guardan**: si el servidor se reinicia, hay que volver a entrar. Los PIN (su hash) sí se guardan. | — |
| S-92 | Hay un solo proceso de servidor escribiendo la base. No hay varios servidores a la vez. | — |
| S-94 | Si la base no tiene ninguna credencial, el servidor de demo crea PINs y una contraseña de admin **de demo** y los muestra al arrancar. Solo para uso local: con datos reales hay que cambiarlos. *(Detectado al probar el arranque: con una base nueva nadie podía entrar.)* | — |
| S-93 | Al cargar la base solo se reconstruyen objetos del propio sistema. Si la base fue alterada para crear otra cosa, la carga se rechaza. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| PS-01 | Guardar y volver a cargar devuelve **exactamente** el mismo estado: pedidos, pagos, saldos, reembolsos, zonas, catálogos, reservas, credenciales, liquidaciones, bolsas, entregas, reclamos, colchón y contadores internos. Los montos no pierden decimales y las fechas conservan su zona horaria. | — |
| PS-02 | Guardar es **todo o nada** (una transacción). Si algo falla a mitad, la base conserva la versión anterior completa. | — |
| PS-03 | La web guarda después de cada POST que termina bien (200 o 303). Si el POST falla (403 o 422), no guarda. | — |
| PS-04 | Al arrancar con una base: si el archivo existe, se carga; si no, se crea con los datos del piloto y se guarda. | — |
| PS-05 | Al cargar, solo se aceptan clases del paquete `yapa_sdd`. Cualquier otra cosa se rechaza (S-93). | `PERSISTENCE_INVALID_DATA` |
| PS-06 | Después de cargar, el sistema sigue igual que antes de apagarse: el siguiente pedido recibe el número que le tocaba y los códigos de operación usados siguen bloqueados. | — |

## Criterios de aceptación

- **PA-01 · Ida y vuelta simple.** Guardar y cargar el store piloto da un estado igual al original. → PS-01
- **PA-02 · Ida y vuelta completa.** Se arma un escenario con:
  - 20 pedidos liquidados;
  - una devolución de saldo pedida;
  - una zona creada por un vecino;
  - un catálogo publicado para W39;
  - el PIN de un vecino;
  - una bolsa armada.

  Al guardarlo y cargarlo, **cada** parte del estado es igual a la original y los montos siguen siendo `Decimal`. → PS-01
- **PA-03 · Continuidad.** Después de cargar, el siguiente pedido es el n.º 21, un código de operación ya usado da `PAYMENT_CODE_ALREADY_USED`, y el vecino entra con su PIN. → PS-06
- **PA-04 · Todo o nada.** Si guardar falla a mitad, la base sigue teniendo la versión anterior completa. → PS-02
- **PA-05 · Base alterada.** Una base con una clase ajena al sistema → `PERSISTENCE_INVALID_DATA`, sin ejecutar nada. → PS-05
- **PA-06 · La web guarda.** Después de registrar un pedido desde la web, otra carga de la base lo tiene. Después de un POST que falla (422), la base no cambia. → PS-03
- **PA-07 · Arranque.** Sin archivo, `open_store` crea la base con el piloto. Con archivo, carga lo guardado. → PS-04

## Cómo usarla

```bash
PYTHONPATH=src python -m yapa_sdd.web --base yapa.db --ahora 2026-09-16T10:00:00-05:00
```

La primera vez crea `yapa.db` con el piloto y las credenciales de demo (S-94). Las siguientes veces carga lo guardado.

## Trazabilidad

| Regla | Código | Prueba (`tests/test_persistence.py`) |
|---|---|---|
| PS-01 | `persistence.py` `_encode`, `_decode`, `save`, `load` | `test_pa01_*`, `test_pa02_*` |
| PS-02 | `persistence.save` (`with conn:` → commit o rollback) | `test_pa04_*` |
| PS-03 | `web/app.py` `on_change` después de un POST con 200 o 303 | `test_pa06_*` |
| PS-04, S-94 | `persistence.open_store` · `web/__main__.py` `_demo_credentials` | `test_pa07_*` + prueba manual con el servidor real |
| PS-05, S-93 | `persistence._class_for` (solo dataclasses de `yapa_sdd`) | `test_pa05_*` |
| PS-06 | se guardan los contadores internos y `used_codes` | `test_pa03_*` |

## Prueba manual (24/09/2026)

Se levantó el servidor con `--base` y una base nueva. Por HTTP real se entró como el vecino 101 con PIN, se registró un pedido con el token CSRF, se apagó el servidor y se cargó la base desde fuera: el pedido 1 (S/ 59.60) estaba guardado.

# Iteración 35 · El admin ve qué le espera y encuentra a un vecino

## Requisito

Como admin de Yapa, quiero ver en el menú cuántas cosas esperan mi atención y buscar a un vecino sin recorrer toda la lista.

## Por qué

Recorrido visual del 18/10/2026: el menú tenía 9 secciones sin ninguna señal de pendientes, y el padrón de vecinos solo se podía recorrer a ojo (15 filas en la demo, más en la vida real). Sin supuestos nuevos de negocio.

## Reglas

| Regla | Comportamiento |
|---|---|
| AD-01 | El menú muestra un número junto a **Resumen** (pagos por verificar), **Reclamos** (pendientes) y **Devoluciones** (por devolver). Con 0 no se muestra nada. |
| AD-02 | Los números se actualizan al cambiar de sección y después de cada acción que se completa (verificar, aprobar, pagar). |
| AD-03 | Los lectores de pantalla oyen "3 pendientes", no solo "3". |
| AD-04 | Vecinos tiene un buscador por nombre, número de cliente o celular. No distingue mayúsculas ni tildes. |
| AD-05 | Con texto escrito, el título dice "Vecinos (2 de 15)"; sin coincidencias aparece "Ningún vecino coincide con la búsqueda". |

## Criterios de aceptación (`src/utils/admin.test.ts`, FA-K)

| # | Entrada | Resultado |
|---|---|---|
| FA-K1 | texto vacío | los 3 vecinos |
| FA-K2 | "perez" | solo Ana Pérez |
| FA-K3 | "105" | solo el cliente 105 |
| FA-K4 | "9112" | solo el celular 911222333; un vecino sin celular no rompe |
| FA-K5 | "zzz" | lista vacía |

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| AD-01..AD-03 | `refreshPending` y el menú en `AdminPanel.tsx` | navegador: Resumen 3 y Devoluciones 2, igual que las tablas |
| AD-04, AD-05 | `filterNeighbors` en `src/utils/admin.ts`, `Neighbors` | FA-K1..FA-K5; navegador: "ana" → 2 de 15, "zzz" → 0 de 15 y mensaje |

Evidencia: `docs/evidencia/desarrollo/35-busqueda-rojo.txt` y `35-busqueda-verde.txt`.

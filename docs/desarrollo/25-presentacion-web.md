# Iteración 25 · Presentación de la web y semana de demo

## Requisito

Como vecino, quiero entender en segundos qué es Yapa, ver qué tan cerca está el grupo del siguiente descuento y cuánto ahorro frente al supermercado, para confiar en el precio que pago.

Como equipo, queremos mostrar la web con una semana ya vivida (pedidos, entrega, liquidación y "te devolvemos"), sin tener que cargar todo a mano antes de cada demo.

## Por qué

- La web (iteraciones 9 a 24) cumple las reglas, pero se ve como un formulario. El vecino no ve de un vistazo la promesa del precio máximo (C-01) ni el avance del tramo (C-02), que son la razón para pedir en Yapa.
- Con la base vacía, el catálogo dice "0 de 100 kg" y Mi cuenta no tiene ahorro que mostrar. Para enseñar la liquidación hay que hacer una semana completa a mano.
- La web sigue siendo un **adaptador**: esta iteración no cambia ninguna regla de negocio, solo cómo se muestran los datos que ya existen.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-139 | El distintivo de ahorro del catálogo compara el **precio máximo** de Yapa con el precio de referencia vigente. Es el peor caso: el ahorro real, después de liquidar, es igual o mayor. Solo se muestra si el ahorro es positivo; el precio de referencia se sigue mostrando siempre (pregunta 64). | — |
| S-140 | La web no carga nada de otros sitios (fuentes, imágenes, scripts): usa la fuente del sistema y un logo dibujado en la misma página. Así funciona sin internet y no se avisa a terceros de quién la visita. | — |
| S-141 | La semana de demo usa vecinos ficticios y los precios del supermercado medidos el 24/09/2026 (Plaza Vea, `docs/analisis/08_validacion_economica.md`). **No** carga precios del mercado de barrio, porque todavía no se midieron (kit de campo). | — |
| S-142 | La semana de demo se arma solo con los casos de uso existentes (registrar, verificar, armar, entregar, liquidar), en el mismo orden que una semana real. No escribe datos por fuera de ellos, así la conciliación del dinero da 0. | — |
| S-143 | Con `--demo` la hora queda fija en el miércoles 30/09/2026 a las 10:00 (ciclo 2026-W40 abierto), salvo que se indique otra con `--ahora`. Los datos viven en memoria; `--demo` no se combina con `--base`. | — |

## Reglas

| Regla | Comportamiento |
|---|---|
| PW-01 | Toda página tiene la marca (logo y nombre) y la navegación. El enlace de la página actual se marca con `aria-current="page"`. |
| PW-02 | La portada, sin sesión, explica Yapa en tres pasos (pides hasta el miércoles 20:00, compramos juntos al por mayor, recibes el sábado y te devolvemos lo ahorrado) y la promesa "Nunca pagas más del precio que ves" (C-01). Mantiene el botón "Entrar para pedir". |
| PW-03 | Cada producto del catálogo muestra una barra de avance hacia el siguiente tramo: lo pedido entre todos sobre la cantidad del tramo. Si ya está en el mejor precio, la barra queda llena. El texto del avance (WB-01) no cambia. |
| PW-04 | Si un producto tiene un precio de referencia vigente más caro que el precio máximo de Yapa, el catálogo muestra el distintivo "N % menos que en <fuente>" (S-139). |
| PW-05 | En Mi cuenta, el saldo y lo devuelto con Yapa se muestran destacados arriba, antes de los formularios. |
| PW-06 | El panel del administrador muestra sus secciones como accesos con una línea que dice para qué sirve cada una. |
| PW-07 | Ninguna página carga recursos de otro sitio (S-140). |
| PW-08 | `python -m yapa_sdd.web --demo` arranca con la semana de demo (S-141..S-143): la semana 2026-W39 entregada y liquidada, y la 2026-W40 abierta con pedidos. |

## Criterios de aceptación

Hora fija: miércoles 16/09/2026 a las 10:00 (ciclo 2026-W38 abierto) y catálogo base del piloto, salvo que se diga otra cosa.

- **PW-A · Portada.** `GET /` sin sesión muestra "Cómo funciona", los tres pasos, "Nunca pagas más del precio que ves", el botón "Entrar para pedir" y el logo (`class="logo"`). → PW-01, PW-02
- **PW-B · Navegación.** En `/` el enlace "Catálogo" tiene `aria-current="page"`; en `/cuenta`, "Mi cuenta"; en `/admin`, "Admin". → PW-01
- **PW-C · Barra de avance.** Después de un pedido con 5 kg de papa amarilla, el catálogo tiene una barra con valor 5 y máximo 100, y sigue diciendo "5 de 100 kg". → PW-03
- **PW-D · Distintivo de ahorro.** Con un precio de supermercado de S/ 7.99 para la papa amarilla (Plaza Vea), el catálogo muestra "49.6 % menos que en Plaza Vea" (máximo S/ 4.03). Con un precio de S/ 3.00 no aparece ningún distintivo, pero sí el precio de referencia. → PW-04, S-139
- **PW-E · Mi cuenta.** El saldo aparece en el bloque destacado (`class="hero-balance"`) antes del formulario de devolución. → PW-05
- **PW-F · Panel del admin.** `/admin` muestra los accesos a Armado y entrega, Reclamos, Colchón, Métricas, Devoluciones, Conciliación, Catálogo, Precios de referencia y Vecinos, cada uno con su descripción (`class="tiles"`). → PW-06
- **PW-G · Sin recursos externos.** Portada, entrar, Mi cuenta y admin no tienen `src="http`, `href="http`, `@import` ni `url(`. → PW-07
- **PW-H · Semana de demo.** Con la semana de demo: la conciliación da diferencia 0; el pedido de Ana Torres (101) en 2026-W39 está `LIQUIDADO` y le devolvió más de S/ 0; la semana 2026-W40 tiene al menos 5 pedidos; la papa amarilla tiene precio de supermercado vigente el 30/09/2026; no hay precios del mercado de barrio. → PW-08, S-141, S-142
- **PW-I · Demo por la web.** Con la semana de demo y la hora del 30/09/2026 a las 10:00, Ana entra y Mi cuenta muestra "Con Yapa ya te devolvimos" y "En el supermercado costaba". El catálogo muestra el distintivo de ahorro de la papa amarilla. → PW-04, PW-05, PW-08

## Cómo usarla

```bash
PYTHONPATH=src python -m yapa_sdd.web --demo
# abrir http://127.0.0.1:8000 · vecina Ana (101) y admin: credenciales impresas al arrancar
```

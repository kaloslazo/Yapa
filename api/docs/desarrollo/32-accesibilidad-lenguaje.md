# Iteración 32 · Accesibilidad y lenguaje claro de la tienda

## Requisito

Como persona que usa teclado, lector de pantalla, el celular al sol o tiene baja visión, quiero ver dónde estoy, leer todos los textos y entender los avisos. Como vecino o admin, quiero textos en palabras de negocio, sin comandos ni códigos de ley.

## Por qué

Auditoría de diseño del 18/10/2026 (revisión de código y cálculo de contraste con la fórmula WCAG 2.x):

- `input:focus-visible, select:focus-visible { outline: none }` quitaba el foco de las listas y de la subida de foto en Mis pedidos y Mi zona: con teclado no se veía dónde estaba el cursor.
- El gris de apoyo `--muted` (#6b7771) da contraste 3.5 a 4.2 sobre cinco de los siete fondos de la tienda (el mínimo es 4.5).
- El anillo de foco global (acento al 45 %) rinde unos 2.3:1 sobre el fondo; el mínimo para componentes es 3:1.
- El enlace "Saltar al contenido" apuntaba al catálogo y no existe en Carrito, Pedidos ni Zona.
- Las categorías se anunciaban como pestañas sin tener paneles.
- Si el motor no responde, el vecino veía un comando de Python.
- Los avisos desaparecían a los 3,2 segundos, también los de advertencia.
- Columnas de acciones sin encabezado, estados de reclamo en mayúsculas crudas y una etiqueta "Ley 29733" visible en el alta de vecinos.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-175 | Todo texto de apoyo tiene contraste mínimo 4.5:1 sobre cada fondo de la tienda. El gris pasa a #526059 (el más bajo da 4.88:1). | 4.5:1 |
| S-176 | El anillo de foco es de color sólido (el acento oscuro, 5.3:1 o más sobre cualquier fondo) y se ve en todos los campos. | 3:1 mínimo |
| S-177 | Los avisos duran 6 segundos y los de advertencia 9, y los de advertencia se leen en voz alta de inmediato. | 6 s y 9 s |
| S-178 | El aviso de "sin conexión" no muestra comandos al público: dice que no se pudo conectar y ofrece reintentar. El comando solo se muestra en desarrollo. | — |

## Reglas

| Regla | Comportamiento |
|---|---|
| AC-01 | Ningún campo (`input`, `select`, `textarea`) pierde el contorno de foco. |
| AC-02 | `--muted` tiene contraste ≥ 4.5 sobre `--canvas`, `--page`, `--paper`, `--paper-strong`, `--accent-soft`, `--green-soft` y `--yellow-soft`. |
| AC-03 | El color del anillo de foco tiene contraste ≥ 3 sobre `--canvas`, `--page`, `--paper` y `--paper-strong`. |
| AC-04 | "Saltar al contenido" lleva el foco al contenido principal de la página abierta (catálogo, canasta, pedidos o zona). |
| AC-05 | El filtro de categorías son botones con estado "presionado", no pestañas. |
| AC-06 | Aviso sin conexión: "No pudimos conectar con Yapa" y botón **Reintentar** (recarga los datos). |
| AC-07 | Avisos: 6 s; advertencias: 9 s y con `role="alert"`. |
| AC-08 | Las columnas de acciones sin título llevan el título "Acciones" solo para lector de pantalla. |
| AC-09 | El historial de reclamos del admin muestra "Aprobado" o "Rechazado", no la palabra cruda. |
| AC-10 | El alta de vecino dice "Consentimiento del vecino", no la ley. |
| AC-11 | Los montos grandes (pago, devuelto, conciliación) usan cifras de ancho fijo para no saltar. |

## Fuera de esta iteración

Foto del reclamo para el admin y confirmaciones del admin (iteración 33), kickers sobre los títulos y fotos reales de productos.

## Criterios de aceptación (pruebas de `src/**/*.test.ts`)

| # | Criterio | Resultado |
|---|---|---|
| AC-A | `--muted` contra los siete fondos | todos ≥ 4.5 |
| AC-B | color del foco contra cuatro fondos | todos ≥ 3 |
| AC-C | `styles.css` no contiene `outline: none` para `input:focus-visible` ni `select:focus-visible` | cierto |
| AC-D | la flecha de las listas usa el mismo gris que `--muted` | cierto |
| AC-E | `toastDuration('warning')` y `toastDuration('success')` | 9000 y 6000 |

Las reglas de pantalla se verifican en el navegador y quedan en el registro.

## Trazabilidad (regla → código → prueba)

| Regla | Código | Prueba |
|---|---|---|
| AC-01 | se quitó `input:focus-visible, select:focus-visible { outline: none }` de `styles.css` | AC-C; navegador: la lista de reclamos muestra contorno sólido de 3 px |
| AC-02 | `--muted: #526059` en `styles.css` | AC-A (siete fondos) |
| AC-03 | `:focus-visible` con `var(--accent-dark)` | AC-B (cuatro fondos) |
| AC-04 | `onClick` del enlace de salto en `App.tsx` | navegador: en Mis pedidos el foco cae en `main#orders-page` |
| AC-05 | `Catalog.tsx` (`role="group"`, `aria-pressed`) | navegador: grupo con la categoría activa en "true" |
| AC-06 | banner con `retry` en `App.tsx` | revisión de código (el comando solo se ve con `import.meta.env.DEV`) |
| AC-07 | `toastDuration` en `src/utils/toast.ts`, `aria-live` dinámico en `App.tsx` | AC-E |
| AC-08, AC-09, AC-10 | `AdminPanel.tsx` (`sr-only` en las columnas, `CLAIM_STATUS`, "Consentimiento del vecino") | revisión de código |
| AC-11 | `font-variant-numeric: tabular-nums` en `styles.css` | revisión de CSS |

Las pruebas leen `styles.css` (por eso `vitest.config.ts` procesa esa hoja). Se comprobó que fallan de verdad: con el gris viejo y con `outline: none` en `input:focus-visible` fallan 8 pruebas.

Evidencia: `docs/evidencia/desarrollo/32-accesibilidad-rojo.txt` y `32-accesibilidad-verde.txt` (27 pruebas del frontend, antes 13). Tipos y build sin errores. El motor no cambió.

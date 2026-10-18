# Iteración 34 · El admin se puede usar en el celular

## Requisito

Como admin de Yapa, quiero revisar y operar desde el celular: ver todas las secciones, leer las tablas completas y poder salir de mi sesión.

## Hallazgos del recorrido a 390 px (18/10/2026)

| # | Hallazgo | Arreglo |
|---|---|---|
| H-1 | Cada opción del menú medía 335 px (el botón heredaba `width: 100%`): solo se veía una sección | ancho según el texto, 44 px de alto, degradado a la derecha y la opción tocada se centra |
| H-2 | El botón Salir estaba oculto en el celular | queda visible como icono de 44 px |
| H-3 | Las tablas de Conciliación y Revisados se cortaban a la derecha | se envuelven para desplazarse; la de Conciliación (2 columnas) ya no exige 620 px |
| H-4 | "Desactivar", "Nuevo PIN", enlaces de texto y resúmenes de pedido medían 21 a 25 px | 44 px en pantallas de 860 px o menos |

## Trazabilidad

| Hallazgo | Código | Prueba |
|---|---|---|
| H-1..H-4 | bloque "Iteración 34" de `src/styles.css`, `AdminPanel.tsx` (envoltorios y `aria-current`) | AC-F en `src/utils/accessibility.test.ts` y navegador a 390 px |

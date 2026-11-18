# Iteración 75 · Seleccionar bolsas y confirmar sus fotos

> **Renumerada el 18/11/2026.** Se escribió el 13/11/2026 como "iteración 64", cuatro horas después de que la 64 de Carlos (`64-operacion-en-el-celular.md`) ya estuviera en el repo, y usó S-327 y S-328, que la 64 ya tenía con otro significado. Pasa a ser la 75 y sus supuestos a S-367 y S-368. Las evidencias se renombraron a `75-bolsas-*.txt` sin cambiar su contenido.
>
> **Estado: retirada.** La iteración 71 dejó de mostrar este selector y la 76 lo borró (S-374).

## Requisito (Aaron, 13/11/2026)

En Armado, mostrar «Agregar bolsa · − 1 +» y un botón pequeño de confirmación a la derecha. Cada bolsa necesita una foto diferente.

## Supuestos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-367 (antes S-327 de esta spec) | El selector indica cuántas bolsas nuevas faltan registrar, con mínimo 1. No baja las bolsas ya guardadas. Una foto por bolsa y la numeración la pone el servidor. | mínimo 1 |
| S-368 (antes S-328 de esta spec) | Cada foto se envía por la API de siempre. Si falla una, se detiene el envío y quedan solo las pendientes; las guardadas no se reenvían. Mientras se envía no se puede editar. | — |

Se conservan los errores existentes: `CYCLE_STILL_OPEN`, `PHOTO_REQUIRED`, `ORDER_NOT_ATTENDED` y `ZONE_ALREADY_CLOSED`.

## Criterios de aceptación

1. Al inicio hay 1 campo de foto; «+» muestra 2, «−» vuelve a 1 y nunca baja de 1.
2. Con 2 bolsas se piden 2 fotos. Se envían en orden y, al terminar, vuelve a 1 campo vacío.
3. Si se guarda la primera y falla la segunda, queda pendiente solo la segunda; reintentar no duplica la primera.
4. El selector y confirmar tienen nombres accesibles, se usan con teclado y se bloquean durante el envío.
5. Cambiar de semana o de pedido reinicia el borrador.

## Trazabilidad (mientras existió)

- Criterios 1 a 4: `BagForm.tsx` y sus cinco pruebas en `BagForm.test.ts` (ambos borrados en la 76).
- Criterio 5: `Packing` usaba una clave de semana y pedido.
- Evidencia: `75-bolsas-rojo.txt` y `75-bolsas-verde.txt`. TypeScript, 175 pruebas de la web y build.

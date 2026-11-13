# Iteración 63 · Paneles y Explorar más claros

## Requisito (Aaron, 11/11/2026)

Mostrar fechas en Armado, filtrar sus pedidos y entregas por zona, añadir Completados en Reclamos, seguimiento con avisos en Portería, edición organizada de la lista del proveedor y contenido plegable en Explorar. Compras y Reparto conservan sus pantallas y operaciones.

## Alcance y supuestos a validar por el equipo

- S-322: Armado muestra el rango lunes–domingo y año; los códigos ISO siguen viajando a la API. El selector compartido conserva su presentación anterior en Compras.
- S-323: la portería conserva el acceso exclusivo a su zona (S-293). Puede filtrar su tarjeta por estado. Preparación y listo para despacho se deducen de las bolsas; en camino, llegada, recepción y falla usan los registros existentes. No se crea un estado manual «en pausa» ni se cambian las reglas de despacho.
- S-324: Portería consulta cada 15 segundos, al volver a la pestaña y al actualizar manualmente. Avisa dentro de la app por cada nuevo hito observado, incluidos varios entre consultas. No avisa por el historial inicial ni al cambiar de semana. No son notificaciones push del navegador.
- S-325: Proveedor edita productos y tramos con campos, conserva códigos y proveedor de origen, puede añadir productos y quitar filas del borrador. La API sigue validando y el admin sigue aprobando. No se publican productos automáticamente.
- S-326: en Explorar, «Compra con más idea» es un desplegable cerrado al inicio con una frase y foto; las diez preguntas se conservan en dos columnas de escritorio y se muestran cinco al inicio, con un botón para ver las demás. Cómo funciona conserva la lista completa.

## Criterios de aceptación

| Criterio | Resultado |
|---|---|
| PA-01 | W40 de 2026 se muestra como 28 sep–4 oct 2026 en Armado; W01 cruza el año correctamente. Compras conserva su selector. |
| PA-02 | Elegir Z-LINCE-01 filtra tanto las entregas como las bolsas, sin alterar los datos ni las acciones. Cambiar de semana restablece la zona. |
| AT-01 | Completados siempre aparece con contador y vacío útil; aprobados y rechazados conservan resultado e importe, sin acciones nuevas. |
| PO-01 | Recepción añade hitos cronológicos sin exponer productos, precios ni otras zonas; la entrega sigue siendo necesaria para confirmar. |
| PO-02 | Un hito nuevo genera un aviso una vez; cambiar de semana o una primera carga no genera avisos históricos. Polling se limpia al salir. |
| PV-01 | Una lista con múltiples tramos sobrevive a abrir, editar y serializar sin perder datos. Código repetido, cantidad inválida y tramos inválidos impiden envío con explicación. |
| PV-02 | Se puede crear una fila, editar kg/unidades, máximo, paso y precios por volumen, y enviar la propuesta por el endpoint existente. |
| EX-01 | La barra de guías abre/cierra con teclado; mantiene las tres guías corregidas del main. FAQ muestra cinco preguntas y permite ver las diez. |

## Validación prevista

Pruebas de comportamiento frontend y recepción del motor, suite de regresión, TypeScript, build y revisión en localhost en escritorio y móvil. No se modifican las reglas de dinero ni se publica en producción.

## Resultado y trazabilidad

| Criterio | Implementación | Evidencia |
|---|---|---|
| PA-01 | `src/utils/week.ts: weekRangeLabel`, `Packing` usa `CycleSelect dates` | `week.test.ts`; selector con W39/W40 en navegador |
| PA-02 | `AdminPanel.tsx: Packing`, filtro conjunto de paradas y pedidos | `operations.test.ts`, dos zonas y cambio de semana; navegador con Z-LINCE-01 |
| AT-01 | `AdminPanel.tsx: Claims`, tarjeta Completados siempre visible | `operations.test.ts`, vacío y aprobado/rechazado; navegador |
| PO-01 | `reception.py: for_zone`, campos aditivos seguimiento e hitos; `ReceptionCard.tsx` | `test_paneles_63.py`; permisos en `test_personal_por_rol.py` |
| PO-02 | `PartnerPanel.tsx: ConciergeHome`, sondeo, cola de avisos y limpieza; `receptionUpdates.ts` | `operations.test.ts`, dos cambios entre consultas; `receptionUpdates.test.ts`; actualización real en navegador desde otra sesión |
| PV-01, PV-02 | `SupplierListEditor.tsx`, `supplierDraft.ts`, endpoint de propuestas existente | `supplierDraft.test.ts`, `operations.test.ts`; se editó 400→450 kg y añadió Zapallo de prueba en la demo, ambos quedaron En revisión tras recargar |
| EX-01 | `ShoppingGuides.tsx`, variante compacta de `FrequentlyAskedQuestions`, estilos acotados | `guides.test.ts`; cierre con Enter, apertura, cinco/diez preguntas e imágenes en navegador |

- `63-motor-rojo.txt` y `63-web-rojo.txt`: evidencia previa a la implementación.
- `63-motor-verde.txt`: 718 pruebas del motor aprobadas, Python 3.12 con PyJWT, cryptography y tzdata en `.venv` local.
- `63-web-verde.txt`: TypeScript, 169 pruebas en 25 archivos y build aprobados con Node 22.23.4. Permanece el aviso anterior de chunk de más de 500 kB.
- Revisión visual: escritorio y viewport móvil 390×844 (375 px útiles por la barra de desplazamiento), sin desborde horizontal en Proveedor, Portería ni las guías. La propuesta enviada y la recepción confirmada solo modificaron la demo en memoria.
- `DriverRoute` y `Purchases` se compararon con `origin/main`: sus cuerpos no cambiaron. Tampoco cambia la presentación del selector en Compras.
- Los estados de Portería se derivan de hechos del motor. «En pausa» y acceso de una portería a varias zonas necesitan decisiones y permisos adicionales. Los avisos requieren tener la página abierta; no son notificaciones push.
- Localhost ejecuta ahora `Yapa-publicacion` (5173 y 8010). La copia ZIP anterior permanece intacta. No se incluyen secretos, `.venv`, fotos, bases ni `node_modules` en los commits.

# Guía para la reflexión final (sección 21 del enunciado)

El enunciado pide que las respuestas se basen **en la experiencia real** y no solo en la teoría. Para cada pregunta hay puntos de apoyo sacados de lo que pasó en este proyecto, con la evidencia donde se puede mostrar. Cada integrante debería poder responder cualquiera de ellas con sus propias palabras.

---

## 1. ¿Qué cambió en nuestra manera habitual de desarrollar software?

- **Antes:** leíamos el requisito y programábamos. Las dudas se resolvían en el momento, dentro del código y sin dejar registro. La iteración 1 lo muestra: la spec, el código y los tests entraron en el mismo commit.
- **Ahora:** primero escribimos lo que no estaba claro. Salieron 12 decisiones y 12 supuestos con valores concretos (`docs/sdd/10-clarificaciones-v2.md`), y después las reglas, los criterios, el diseño, las pruebas y el código, en ese orden (`git log`).
- **Un cambio concreto:** dejamos de preguntar "¿cómo lo programo?" y empezamos a preguntar "¿qué debe pasar exactamente en este caso?". Por ejemplo: ¿las 20:00:00 están dentro o fuera del ciclo?, ¿el mínimo se compara con el monto redondeado?

## 2. ¿Qué ventajas encontramos?

- **Encontró errores de negocio antes del código.** El cobro en la puerta (RN-21) chocaba con la Ley 29571. Si hubiéramos programado primero, habríamos construido algo ilegal.
- **Nos obligó a validar con datos.** Al especificar el catálogo vimos con precios reales que los abarrotes de marca no dejan margen, y que los frescos sí.
- **Hay trazabilidad verificable.** Cada regla tiene un criterio, un archivo y línea, y una prueba (`docs/sdd/06-trazabilidad.md`). Cualquiera del grupo puede defender cualquier línea.
- **El contrato es claro.** Las pruebas verifican el código de error, no el texto del mensaje, así que se puede cambiar un mensaje sin romper nada.
- **Sirve para la continuidad.** Otra persona, o un asistente de IA, puede continuar leyendo los documentos en orden (`docs/sdd/09-prompt-para-siguiente-iteracion.md`).

## 3. ¿Qué dificultades encontramos?

- **Toma más tiempo al inicio.** Especificar bien fue más lento que programar directo.
- **La spec también se equivoca.** El criterio CA-11 pedía un subtotal exacto de S/ 49.99 que era imposible de formar con 12 % de comisión. Lo detectamos al escribir la prueba y corregimos la spec antes del código.
- **Hay casos que ninguna spec anticipa.** Tuvimos que ajustar dos veces a mitad de camino: la cotización y el faltante en un pedido no entregado.
- **Algunas decisiones no son técnicas.** Montos mínimos, comisión y envío dependen del negocio. Tuvimos que marcarlos como supuestos a validar.
- **Pasar las pruebas no prueba todo.** La revisión manual de casos borde encontró 3 fallos que ninguna prueba cubría (NaN, Infinity, monto no numérico).

## 4. ¿Qué impacto tuvo sobre el diseño del código?

- Las reglas quedaron separadas de la consola y del almacenamiento: `domain`, `cycle`, `store`, `order_registration`, `settlement`, `cli` (`docs/sdd/12-diseno.md`).
- Como la spec dice que el precio lo pone el sistema, `register_order` **no recibe precio**: el diseño hace imposible ese error.
- El orden de validación está especificado (S-11), así que el código sigue ese orden de forma explícita.
- La propiedad "nunca se paga de más" se volvió un invariante con su propia prueba (CL-08).

## 5. ¿Qué impacto tuvo sobre la calidad?

- **45 pruebas**, una o más por criterio, incluyendo fronteras: 19:59:59 frente a 20:00:00, S/ 49.99568 frente a S/ 50.008, el último kilo de stock.
- En la iteración 1 encontramos **14 discordancias** entre la spec y el código (`docs/analisis/02_discordancias_spec_codigo.md`). En la iteración 2, la matriz de trazabilidad y la checklist de convergencia sirven para evitarlas.
- La demo usa los mismos datos que las pruebas, así que lo que se muestra en vivo está verificado.

## 6. ¿La utilizaríamos nuevamente?

Sí, pero dosificada:

- La usaríamos **completa** en la lógica de negocio: cobros, precios, reglas de negocio.
- La usaríamos **más liviana** en cosas simples, como pantallas o listas, donde escribir una spec formal cuesta más de lo que aporta.
- Lo que sí mantendríamos siempre: escribir las dudas antes de programar y cambiar primero la spec cuando algo cambia.

## 7. ¿En qué tipo de proyectos sería más apropiada?

- **Muchas reglas de negocio:** proyectos donde un error cuesta dinero o tiene riesgo legal, como pagos, precios o reservas.
- **Varias personas o equipos involucrados:** negocio, desarrollo, QA, o varios desarrolladores que tienen que entender lo mismo.
- **Requisitos que cambian:** la spec deja registrado qué cambió y por qué.
- **Desarrollo asistido por IA:** una spec clara reduce que la IA "invente" reglas. En este proyecto la IA propuso documentos y código, y el equipo aprobó cada decisión de negocio.
- **Menos apropiada:** prototipos rápidos o exploratorios donde todavía no se sabe qué se quiere construir.

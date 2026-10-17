# Guion de la exposición · iteración 2

Presentación: `yapa-sdd-iteracion-2.pptx` (20 diapositivas, ~23 min más preguntas). Las diapositivas solo tienen títulos e imágenes; todo lo que se dice está aquí y en las notas del orador.

El reparto de expositores es una propuesta: el curso evalúa que todos participen y dominen el proyecto.

| # | Diapositiva | Expositor | Min |
|---:|---|---|---:|
| 1 | Portada | Carlos | 0.5 |
| 2 | Una frase, muchas preguntas | Aaron | 1 |
| 3 | ¿Qué es SDD? | Aaron | 1.5 |
| 4 | Las piezas de una especificación | Aaron | 1.5 |
| 5 | Yapa en una semana | Carlos | 1 |
| 6 | Por qué fracasaron otros | Carlos | 1 |
| 7 | SDD encontró un problema legal | Carlos | 1.5 |
| 8 | ¿Alcanza el margen? | Carlos | 1.5 |
| 9 | Una parada por edificio | Carlos | 0.75 |
| 10 | Zonas creadas por vecinos | Carlos | 0.75 |
| 11 | Te devolvemos | Kalos | 1 |
| 12 | Si alguien se retira, Yapa no pierde | Kalos | 1 |
| 13 | De la regla a la prueba | Aaron | 1.5 |
| 14 | Diseño en capas | Aaron | 1 |
| 15 | Spec primero: el historial de Git | Kalos | 1 |
| 16 | De rojo a verde | Kalos | 0.75 |
| 17 | Demo en vivo | Kalos | 3 |
| 18 | Resultados | Carlos | 0.75 |
| 19 | Lo que aprendimos | Carlos | 1 |
| 20 | Cierre | Todos | 1 |

## 1. Portada · Carlos

Buenos días. Somos Carlos, Aaron y Kalos. Nos tocó Specification-Driven Development y lo aplicamos a nuestro proyecto del curso, Yapa. La idea de la exposición es mostrar cómo escribir la especificación antes que el código cambió lo que construimos, no solo cómo lo documentamos.

## 2. Una frase, muchas preguntas · Aaron

Un requisito típico es 'el vecino debe poder registrar su pedido'. Suena claro, pero cada persona del equipo lo entiende distinto: ¿hasta qué hora?, ¿cuánto es el mínimo?, ¿quién pone el precio?, ¿qué pasa si mis vecinos no compran? Si esas respuestas no se escriben, cada uno las decide en su código y el sistema termina inconsistente. Eso es lo que SDD busca evitar: requisitos ambiguos, interpretaciones distintas y documentación que no coincide con el código.

## 3. ¿Qué es SDD? · Aaron

Specification-Driven Development pone la especificación en el centro. Partimos de una necesidad, la convertimos en requisito, y el requisito en una especificación verificable: entradas, salidas, reglas y errores. De ahí salen los criterios de aceptación, el diseño, el código y la validación contra esos mismos criterios. La flecha naranja es lo más importante: si algo cambia, no se parcha el código; se cambia primero la spec y de ahí baja el cambio. Diferencia con TDD: en TDD la prueba dirige; en SDD la especificación dirige, y las pruebas son una forma de verificarla.

## 4. Las piezas de una especificación · Aaron

Estas son las cinco piezas y cómo se ven en Yapa. El requisito es la necesidad del usuario. La especificación la vuelve verificable. La regla de negocio es una condición que siempre se cumple, por ejemplo RP-10: el subtotal exacto debe ser al menos 50 soles. El criterio de aceptación es el escenario que lo prueba: con 49.99568 se rechaza, aunque redondeado daría 50. Y el contrato es la firma del componente: qué recibe y qué devuelve, incluido el código de error. Así respondemos la pregunta de requisito versus especificación: el requisito dice qué se necesita; la especificación dice exactamente cómo se comporta el sistema.

## 5. Yapa en una semana · Carlos

Yapa junta los pedidos de vecinos de Lince, Jesús María y La Victoria. De lunes a miércoles cada uno arma su pedido y paga por adelantado el precio máximo. El miércoles a las 20:00 se cierra, el jueves se compra al proveedor aliado, el viernes se arma cada bolsa y se le toma foto, y el sábado se entrega en la portería de cada edificio. Después viene lo que llamamos 'te devolvemos': lo que se ahorró entre todos vuelve como saldo.

## 6. Por qué fracasaron otros · Carlos

Antes de escribir reglas revisamos proyectos parecidos que cerraron. Favo, en Perú, agrupaba por distrito y nunca logró margen por pedido. Muni tenía un costo de adquisición alto y ticket bajo. Merqueo y Missfresh cargaban inventario y almacenes propios. Meituan Youxuan dependía de subsidios: cuando se prohibió vender bajo costo, el volumen cayó. Cada una de estas lecciones se convirtió en una regla: mínimo por zona, cero inventario, nunca subsidiar, margen por pedido.

## 7. SDD encontró un problema legal · Carlos

Al escribir la especificación del cobro encontramos que nuestro propio modelo de negocio cobraba en la puerta la diferencia cuando el peso real salía mayor, y si el cliente no pagaba, no recibía su pedido y quedaba suspendido. La Ley 29571, artículo 4.2, prohíbe cobrar recargos sobre el precio fijado. Si hubiéramos programado primero, ese error estaría en el código. Con SDD lo cambiamos en la spec: el cliente paga el precio máximo, nunca más de lo que vio, y la diferencia se le devuelve. Este es nuestro mejor ejemplo de qué pasa cuando cambia una especificación.

## 8. ¿Alcanza el margen? · Carlos

También validamos con precios reales. En abarrotes de marca, el supermercado vende casi a costo: con nuestra comisión, Yapa saldría más cara en 7 de 8 productos, hasta 25 por ciento más. En cambio, en frescos resistentes como papa, cebolla, ajo o limón, el ahorro para el cliente queda entre 36 y 67 por ciento. Esta evidencia cambió la especificación del catálogo: el piloto se enfoca en frescos resistentes y limpieza de marcas emergentes.

## 9. Una parada por edificio · Carlos

Entregar casa por casa con un courier cuesta entre 8 y 15 soles por pedido. Si el camión hace una sola parada por edificio y deja todo en la portería, el costo baja a entre 0.89 y 2.60 soles. Por eso la zona en Yapa no es un distrito: es un punto de recepción.

## 10. Zonas creadas por vecinos · Carlos

Un vecino crea la zona, registra el punto de recepción y a la persona que recibe. Si dos zonas están cerca, pueden unirse para llegar juntas al mínimo de 8 pedidos, pero cada una mantiene su parada. Si una zona está a más de 500 metros, no se une porque el camión perdería tiempo y dinero.

## 11. Te devolvemos · Kalos

Este es un pedido de nuestras pruebas de aceptación. El vecino pagó 61 soles, el precio máximo. Entre todos se alcanzaron tramos de descuento en papa amarilla, papa blanca y cebolla: 9.86 soles menos. El envío se repartió entre 20 pedidos de la zona: 3 soles menos. El costo real fue 48.14 y le devolvemos 12.86 como saldo. Todos estos números salen del código y los verifica una prueba.

## 12. Si alguien se retira, Yapa no pierde · Kalos

Un riesgo era: si alguien compra con el precio de descuento y luego otros se retiran, ¿quién paga la diferencia? Lo resolvimos en la spec: todos pagan el precio máximo y el precio final se calcula al cierre. Si alguien se retira y bajamos de 100 a 95 kilos, el precio vuelve al máximo, pero nunca lo supera. Esa propiedad está escrita como criterio CL-05 y CL-08 y tiene su prueba.

## 13. De la regla a la prueba · Aaron

Así recorremos una especificación de punta a punta, que es lo que pide el curso. La decisión de negocio está en el documento de clarificaciones. La regla RP-10 está en la spec. El criterio CA-11 describe el caso de frontera. El código está en order_registration.py, línea 116. La prueba se llama igual que el criterio. Y se puede ver en vivo con la consola. La matriz completa, con las 24 reglas, está en docs/sdd/06-trazabilidad.md.

## 14. Diseño en capas · Aaron

La spec nos llevó a separar responsabilidades. Las reglas del registro y de la liquidación viven en sus propios módulos y no dependen de la consola ni del almacenamiento. El repositorio es en memoria, pero se puede cambiar por una base de datos sin tocar las reglas. Además, como la spec dice que el precio lo pone el sistema, la función de registro ni siquiera recibe precio: es imposible que el cliente lo mande.

## 15. Spec primero: el historial de Git · Kalos

El historial muestra el orden real del trabajo: primero clarificaciones, especificación, criterios y diseño; después las pruebas; y recién al final el código. Cuando a mitad de camino descubrimos un caso nuevo, por ejemplo un faltante reportado para un pedido que nunca se entregó, primero entró como cambio de spec, luego como prueba y después como código.

## 16. De rojo a verde · Kalos

Guardamos la salida de cada momento en docs/evidencia. Primero, las 42 pruebas escritas fallaban porque el código no existía. Luego implementamos el registro y quedó solo la liquidación pendiente. Al final, con la liquidación y la revisión de casos borde, las 45 pruebas pasan. En esa revisión encontramos tres fallos que ninguna prueba cubría, como una cantidad NaN que hacía caer el programa, y los corregimos agregando primero su prueba.

## 17. Demo en vivo · Kalos

Aquí salimos a la terminal. Primero cotizamos un pedido y lo registramos. Luego mostramos tres rechazos: un pedido a las 20:00 en punto, uno bajo el mínimo que dice cuánto falta, y uno de una zona fuera del piloto. Por último, ejecutamos un ciclo completo: veinte vecinos de Jesús María reciben saldo, el pedido que no verificó su pago queda cancelado, y el grupo de Lince, que no llegó a 8 pedidos, recibe reembolso total. Esta imagen es la salida real, por si falla el proyector.

## 18. Resultados · Carlos

En resumen: 24 reglas especificadas, 24 criterios de aceptación, 45 pruebas en verde y 16 commits en el orden docs, test, feat. Lo que no afirmamos: no probamos integración real con Yape o Plin, que no tienen API pública, ni validamos todavía los precios del mercado de barrio, que es el competidor real en frescos.

## 19. Lo que aprendimos · Carlos

Tres lecciones. Primero, preguntar antes de programar: escribir 12 decisiones y 12 supuestos nos evitó construir un cobro ilegal. Segundo, cada regla con su prueba: así cualquiera puede verificar que el código cumple lo que dice la spec. Tercero, cuando algo cambia, se cambia primero la spec. La dificultad fue el tiempo: especificar bien toma más que programar directo, y una spec equivocada produce código coherente pero equivocado. Lo usaríamos de nuevo en proyectos con reglas de negocio y varias personas involucradas.

## 20. Cierre · Todos

Gracias. Quedamos atentos a sus preguntas. (Guía de defensa: docs/07-trazabilidad-defensa.md)

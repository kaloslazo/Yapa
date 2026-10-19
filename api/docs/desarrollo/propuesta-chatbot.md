# Propuesta: chatbot de Yapa

Documento para que el equipo decida. No es una iteración: no hay código ni supuestos nuevos todavía. Escrito el 19/10/2026.

## Recomendación en una frase

**No construir un chatbot general todavía.** Primero medir qué preguntan de verdad los vecinos y los admins de zona durante el piloto; después, si hace falta, sumar una ayuda dentro de la app que responda con los datos de cada persona. Un modelo de lenguaje solo entra si lo medido muestra preguntas que esa ayuda no resuelve.

## Qué sabemos y qué no

- **No hay todavía un dolor observado.** No hemos corrido el piloto con vecinos reales, así que todo lo de abajo son hipótesis sacadas de las pantallas y del recorrido de una semana, no de lo que la gente pregunta.
- Lo que ya existe y cubre parte del problema: los **avisos** dentro de la app y por correo (iteración 42), el **Olvidé mi PIN** con código (iteraciones 39 y 40) y los paneles del admin de zona y del equipo.
- Cuando no hay chatbot, la persona le escribe a alguien por WhatsApp. Esa es la carga que un bot aliviaría, y es lo que hay que medir.

## Qué le serviría a cada uno (hipótesis a comprobar)

| Quién | Pregunta probable | ¿Hace falta un modelo de lenguaje? |
|---|---|---|
| Vecino | ¿Mi pedido ya llegó? ¿Verificaron mi pago? | No. Es mirar el estado de su pedido. |
| Vecino | ¿Cuánto me devuelven y a dónde? ¿Cuándo? | No. Está en su liquidación y en su saldo. |
| Vecino | ¿Cuánto falta para que mi grupo llegue al mínimo? | No. Es un número del panel de su zona. |
| Vecino | ¿Cómo reclamo un producto dañado? ¿Hasta cuándo puedo? | No. Son reglas fijas con un botón. |
| Vecino | Preguntas escritas con sus palabras, con errores o mezcladas ("mi bolsa no llegó completa") | **Quizá.** Entender la frase libre es lo único que los botones no hacen bien. |
| Admin de zona | ¿Quiénes de mi edificio todavía no pidieron? | No. Ya está en su panel. |
| Admin de zona | Un mensaje listo para recordarle al grupo que cierra el miércoles | **Quizá.** Una plantilla con el nombre y la hora alcanza; el modelo solo suma variedad de tono. |
| Equipo Yapa | ¿Qué zonas necesitan atención esta semana? | No. Ya lo hace el análisis del panel, con números exactos. |
| Equipo Yapa | Un resumen escrito de la semana | **Quizá.** Pero un resumen escrito por un modelo puede equivocarse en una cifra, y aquí el dinero tiene que cuadrar. |

La mayor parte de lo que se pregunta es "¿cómo va lo mío?". Eso se responde mejor con los datos exactos que con un modelo que redacta: nunca se equivoca en un monto y cuesta cero por consulta.

## Lo que el bot no haría nunca

Estas reglas valen para cualquier versión, con o sin modelo de lenguaje:

1. **Solo lee.** No cobra, no devuelve, no cambia un PIN ni un correo, no cancela pedidos. Si la persona quiere hacer algo, la lleva a la pantalla donde se hace.
2. **Solo habla de la persona que pregunta.** Sin datos de otros vecinos. Lo que ve el admin de zona sigue siendo lo que ya ve en su panel (nombres y si pidió, sin montos).
3. **No inventa precios ni reglas.** Un precio solo se dice si está en el catálogo de la semana (nunca cobrar más de lo que el cliente vio). Si la respuesta no está en los datos o en las reglas escritas, dice "no lo sé" y ofrece hablar con una persona.
4. **Ninguna instrucción escrita por el usuario cambia lo anterior.** Si un modelo de lenguaje lee lo que la gente escribe, hay que asumir que alguien intentará engañarlo; por eso las reglas 1 a 3 las cumple el motor de Yapa, no el modelo.
5. **Datos personales:** si algún día se manda texto de vecinos a un proveedor externo, hay que avisarlo en el consentimiento (Ley 29733) y mandar lo mínimo, sin celular ni correo.

## Tres caminos

| | A. Preguntas frecuentes con botones | B. Entiende frases libres | C. Asistente conversacional completo |
|---|---|---|---|
| Qué es | Una pantalla "Ayuda" con las preguntas comunes; cada una responde con los datos de la persona | Lo mismo, pero la persona escribe y el sistema elige qué pregunta frecuente corresponde | Conversa y redacta con un modelo de lenguaje |
| Costo por uso | Cero | Bajo, pero con costo | El más alto |
| Riesgo de error | Casi nulo | Bajo: solo elige entre respuestas ya escritas | Real: puede redactar algo falso |
| Qué hay que construir | Pantalla y consultas que ya existen | Un clasificador (puede ser un modelo pequeño) más lo de A | Todo lo de B, más controles contra engaños y revisión de respuestas |
| Cuándo | Después del piloto, si lo medido lo pide | Solo si A deja preguntas sin resolver | Muy probablemente no hace falta en esta etapa |

**Mi recomendación:** medir (paso 0), construir A si hay carga que aliviar, y subir a B solo con evidencia. C no se justifica hoy.

## Sobre usar modelos gratuitos o claves personales

No conviene apoyar el producto en un plan gratuito ni en la clave personal de una persona del equipo: los límites y las condiciones de un plan gratuito cambian sin aviso, la clave queda ligada a una cuenta personal y el piloto dependería de ello. Si se llega a B, se usa una cuenta del proyecto, con un tope de gasto mensual y la clave solo en variables de entorno del servidor, nunca en el repositorio ni en el navegador. El proveedor se elige entonces, con precios mirados ese día; no hace falta decidirlo ahora.

## Dónde viviría

- **Dentro de la app** (la opción por defecto): gratis, siempre disponible y con la sesión de la persona, así que ya sabe quién es sin pedirle datos.
- **Por WhatsApp:** es donde la gente ya está, pero hablar con el bot por WhatsApp pasa por la API de WhatsApp Business, que cobra por conversación (unos centavos de dólar por mensaje en Perú según fuentes de terceros, con un aumento anunciado para octubre de 2026). Solo si el volumen lo justifica.

## Qué medir en el piloto (paso 0)

Una hoja simple que llenen los admins de zona y quien atienda el WhatsApp de Yapa durante las primeras semanas: fecha, quién preguntó (vecino, admin de zona), la pregunta con sus palabras y si se pudo responder mirando su cuenta. Al terminar, contar:

- cuántas preguntas por semana y qué porcentaje son "¿cómo va lo mío?" (se resolverían con A);
- cuántas son frases que los botones no entenderían (justificarían B);
- cuántas son otra cosa (un problema del servicio, no del bot).

El equipo decide el umbral para pasar de A a B (por ejemplo, "si más de un tercio de las preguntas no entra en los botones"); no lo fijo yo.

## Decisiones que necesita el equipo

1. ¿Medimos primero (paso 0) o preferimos construir A de entrada?
2. ¿Quién atiende lo que el bot no sabe y en qué horario? Un bot que deriva a nadie es peor que no tener bot.
3. ¿Dentro de la app solamente o también por WhatsApp?
4. ¿El admin de Yapa quiere un asistente para consultar sus datos, o el panel de análisis ya le basta?
5. ¿Aceptamos que, si algún día hay un modelo de lenguaje, los textos de los vecinos viajen a un proveedor externo? Si sí, hay que ajustar el consentimiento.

## Lo que haría yo ahora

Nada de código para el chatbot. Sí dejar la hoja de medición lista para el piloto y, cuando haya datos, volver a este documento con las respuestas reales.

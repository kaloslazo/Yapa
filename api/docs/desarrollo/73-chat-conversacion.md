# Iteración 73 · Preguntas, opciones y última respuesta

S-365 (a validar por el equipo): conservar el chat y el asistente de Kalos. La búsqueda y sugerencias de FAQ funcionan sin IA; consultas personales conocidas conservan el endpoint con datos del vecino. Las consultas libres sin coincidencias ofrecen ayuda segura y la opción explícita de consultar el asistente existente, que puede usar la IA ya configurada. No se añaden proveedores, claves ni servicios.

CH73-1: escribir y enviar una pregunta frecuente muestra la pregunta del usuario y opciones relacionadas; no necesita API. Elegir una opción añade su respuesta vigente de la lista compartida.
CH73-2: preguntas personales siguen consultando /api/asistente; no se inventa información del pedido. Se conservan los rótulos de fuente y las sugerencias del motor.
CH73-3: la respuesta nueva queda al final del área de conversación y se desplaza allí. Las sugerencias no empujan la respuesta fuera de vista. Acceso por teclado, temas, sin coincidencias y vista móvil.
CH73-4: reiniciar invalida respuestas en curso. Se conserva la entrada con Escape y la restauración de foco. Reemplazar el asistente con datos por un FAQ exclusivamente está en pausa por solaparse con la iteración 70.

## Trazabilidad y validación

- CH73-1/2: FaqChatbot y faqSearch; chat73.test y regresión de Assistant.test. Se mantienen las sugerencias y fuentes de la API existente.
- CH73-3/4: desplazamiento local del área de conversación, opciones antes del historial, eliminación de la animación de entrada de respuestas y generación de peticiones para descartar respuestas tras reiniciar. FaqChatbot.test y chat73.test.
- 764 pruebas motor (760 aprobadas y 4 omitidas), 214 web, TypeScript y build aprobados: 73-chat-*-verde.txt.
- Chrome a 390 px: pregunta, opciones sin API, cinco respuestas y última respuesta visible, salida segura para una pregunta desconocida. Captura docs/chatbot-faq/chat-17nov.png.

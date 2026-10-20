# Iteración 43 · Correos con diseño

## Requisito

Como vecino, quiero que los correos de Yapa (código de verificación, recuperar el PIN y avisos) se vean cuidados y se lean bien en el celular, con la marca de Yapa y el código bien destacado, para confiar en que el correo es de verdad de Yapa. Como equipo, queremos que siga existiendo la versión en texto plano para quien no vea HTML.

## Por qué

Hoy el correo sale como texto suelto (iteraciones 40 y 42). Con el dominio propio ya funcionando, el correo es la cara de Yapa fuera de la app. Un código escondido en un párrafo se lee mal, sobre todo en el celular.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-222 | El correo real lleva **las dos versiones**: texto plano y HTML. El texto plano es el mismo mensaje de siempre, así que quien no vea HTML lee lo mismo. La consola del motor (sin credenciales) sigue imprimiendo solo el texto. | 2 versiones |
| S-223 | El diseño usa **solo texto y color**, con la marca escrita "Yapa" y los colores de la app: **sin imágenes, sin fuentes externas, sin scripts y sin píxeles de seguimiento**. Así no depende de que el cliente de correo cargue imágenes, no rastrea a nadie y no se rompe si el vecino las bloquea. | sin imágenes |
| S-224 | Si el equipo define la variable de entorno `YAPA_PUBLIC_URL` (la dirección pública de Yapa, que no es secreta), el correo de aviso lleva un botón "Abrir Yapa" que apunta a esa dirección. Es un enlace a la portada, **no un enlace de entrada**: nunca lleva sesión, código ni PIN. Sin la variable, no hay botón. | opcional |
| S-225 | El diseño se arma a partir del mismo texto del correo (no hay una segunda plantilla por tipo de aviso): el código de 6 dígitos se reconoce por la frase "Tu código es N." y se destaca; los demás párrafos se muestran como párrafos. | una plantilla |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| HT-01 | El correo que sale por SMTP es multiparte: una parte `text/plain` idéntica al mensaje de siempre y una parte `text/html`. El remitente, el asunto y el destinatario no cambian. | — |
| HT-02 | **Todo texto que viene de datos se escapa** en el HTML (el nombre del vecino, el título y el texto del aviso). Un nombre como `<script>` se muestra como texto y no se ejecuta. | — |
| HT-03 | En un correo con código, el código de 6 dígitos va en una caja destacada, con letra grande y espaciada, y con la frase de validez (10 minutos). El código no va en el asunto. | — |
| HT-04 | Sin imágenes, scripts, fuentes ni hojas de estilo externas: solo estilos escritos en el propio correo y una estructura de tablas que leen bien los clientes de correo y el celular. | — |
| HT-05 | Los correos de aviso llevan la línea para apagarlos desde Mi cuenta, en el pie. | — |
| HT-06 | El botón "Abrir Yapa" (S-224) solo aparece si `YAPA_PUBLIC_URL` empieza con `http://` o `https://`; cualquier otro valor (por ejemplo `javascript:`) se ignora y no hay botón. El valor se escapa. | — |
| HT-07 | El cuerpo del correo no cambia en la app ni en la API: los avisos, sus textos y las respuestas siguen igual. Solo cambia cómo se ve el correo real. | — |

## Criterios de aceptación (`tests/test_correo_html.py`)

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| HT-A | Dos versiones | `SmtpMailer.send` con un mensaje cualquiera | el mensaje enviado tiene una parte `text/plain` igual al texto original y una parte `text/html` |
| HT-B | Cabeceras | el mismo envío | `From` es `Yapa <remitente>`, `To` y `Subject` son los de siempre |
| HT-C | Se escapa | el texto trae `<script>alert(1)</script>` y un nombre `<b>Ana</b>` | el HTML no contiene `<script` ni `<b>Ana`; contiene el texto escapado |
| HT-D | Código destacado | el mensaje de código con 795704 | el HTML tiene el código en una caja destacada, una sola vez, con "10 minutos" |
| HT-E | Sin imágenes ni scripts | cualquier correo sin `YAPA_PUBLIC_URL` | el HTML no contiene `<img`, `<script`, `<link`, `@import` ni `http` |
| HT-F | Botón | `YAPA_PUBLIC_URL=https://yapa.example` | el HTML tiene un enlace a esa dirección con el texto "Abrir Yapa" |
| HT-G | Botón inseguro | `YAPA_PUBLIC_URL=javascript:alert(1)` | no hay botón ni `javascript:` en el HTML |
| HT-H | Aviso con pie | un aviso de la iteración 42 | el HTML conserva el texto del aviso y la línea de apagar en Mi cuenta |
| HT-I | Orden | un mensaje de varios párrafos | los párrafos salen en el mismo orden y la despedida "Yapa" no aparece como un párrafo más (la marca ya está en el encabezado) |
| HT-J | Consola | `ConsoleMailer.send` | sigue imprimiendo el texto plano, sin HTML |
| HT-K | Variable de entorno | `mailer_from_env` con `YAPA_PUBLIC_URL` | el correo que arma ese mailer lleva el botón (S-224) |

## Fuera de esta iteración

Plantillas distintas por tipo de aviso, imágenes o logotipo, correos en otros idiomas, y medir si abren los correos (S-223 lo descarta a propósito).

# Iteración 47 · Pulido de lanzamiento

## Requisito

Como vecino que abre Yapa desde el celular, quiero que cargue rápido con mis datos móviles y que el enlace que me mandan por WhatsApp se vea bien. Como equipo, queremos un sitio sin errores visibles en la consola y con la información mínima de privacidad que se le debe a quien deja sus datos.

## Por qué (hallazgos de la revisión del 21/10)

- Las imágenes pesaban **3,6 MB** en total (cada producto entre 277 y 582 KB, el banner 696 KB y el logo de 512 px para mostrarse a 36 px). Un vecino con datos móviles descarga todo eso solo para ver el catálogo.
- **No había favicon**: cada visita daba un error 404 en la consola y la pestaña salía sin ícono.
- Al compartir el enlace de invitación por WhatsApp **no había vista previa** (sin etiquetas Open Graph), así que el mensaje de invitación llegaba como un enlace pelado.
- Los archivos con huella de `/assets/` se guardaban solo una hora, aunque nunca cambian.
- El registro pide aceptar el tratamiento de datos (Ley 29733) pero **no había dónde leer qué se guarda y para qué**.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-249 | Las imágenes de la web van en **WebP** y a su tamaño real de uso: productos de 480 px, banner de 760 px y logo de 192 px. Ninguna imagen de `public/images` pesa más de 150 KB. Hay favicon y ícono para el celular. | 3,6 MB → unos 260 KB |
| S-250 | **Vista previa al compartir**: la web declara título, descripción e imagen (1200×630) para WhatsApp y redes. En el enlace de invitación, el motor personaliza el título y la descripción con lo que ya es público en esa página (el primer nombre de quien invita, la zona y cuántos vecinos hay); un enlace que no vale muestra la vista previa general. | vista previa por enlace |
| S-251 | Los archivos de `/assets/` (con huella en el nombre) se guardan **un año**, sin revalidar; el resto, una hora, e `index.html` no se guarda (cambia S-235 solo para `/assets/`). | caché larga con huella |
| S-252 | **Página de privacidad** en `/privacidad` con un texto sencillo: qué datos se guardan, para qué, quién los ve, cuánto tiempo y cómo pedir verlos, corregirlos o borrarlos. El registro enlaza a ella. **Es un borrador que el equipo debe revisar** (en especial el medio de contacto y los plazos). | borrador |

## Reglas

| Regla | Comportamiento |
|---|---|
| PU-01 | Ninguna imagen de `public/images` pesa más de 150 KB y las imágenes propias son WebP (más el JPG de la vista previa y los íconos PNG pequeños). |
| PU-02 | `index.html` declara favicon, ícono para el celular y las etiquetas `og:title`, `og:description`, `og:image`, `og:url`, `og:type` y `twitter:card`, con la imagen en dirección completa. |
| PU-03 | `GET /unete/<código>` sirve `index.html` con `<title>`, `og:title`, `og:description` y `og:url` de esa invitación; con un código que no vale, el `index.html` normal. Todo texto se escapa. No se agrega nada que la página pública de la invitación no muestre ya. |
| PU-04 | Los archivos de `/assets/` llevan `Cache-Control: public, max-age=31536000, immutable`; `index.html`, `no-cache`; los demás, una hora. |
| PU-05 | `/privacidad` muestra la página de privacidad y el consentimiento del registro tiene un enlace a ella, que abre en otra pestaña. |

## Criterios de aceptación

Motor (`tests/test_produccion.py`, ampliado):

| # | Criterio | Entrada | Resultado |
|---|---|---|---|
| PU-A | Vista previa de la invitación | `GET /unete/abc` con un `preview` que devuelve Ana, Edificio Los Álamos y 3 vecinos | el HTML trae `og:title` con "Ana", la zona en la descripción y `<title>` igual; `Content-Type` HTML y `no-cache` |
| PU-B | Enlace inválido | el `preview` falla o devuelve nada | el `index.html` normal, sin el nombre |
| PU-C | Texto escapado | una zona con `<script>` y comillas | no queda ni `<script` ni una comilla suelta dentro del atributo |
| PU-D | Caché de assets | `GET /assets/a.js` | `max-age=31536000` e `immutable`; `index.html` sigue `no-cache` |

Web (`src/publicAssets.test.ts`, `src/components/privacyPage.test.ts` y `src/components/invitePage.test.ts`):

| # | Criterio | Resultado |
|---|---|---|
| PU-E | Peso de las imágenes | ninguna imagen de `public/images` supera 150 KB; ya no hay PNG propios pesados |
| PU-F | `index.html` | tiene favicon, ícono del celular y las etiquetas Open Graph con imagen absoluta |
| PU-G | Privacidad | la página dice qué datos se guardan, para qué, y cómo ejercer los derechos; el registro enlaza a `/privacidad` |

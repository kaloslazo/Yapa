# Iteración 66 · Ver la foto que se toma

## Requisito

Como armador, transportista o vecino que reclama, quiero ver la foto que elegí antes de enviarla, y como armador, ver las fotos de las bolsas que ya registré, para saber que salieron bien sin preguntarle a nadie.

## Por qué

Con la iteración 64 la foto se toma desde un botón grande del celular, pero el botón solo decía "Foto lista": no se veía qué foto se había elegido. En el armado, después de registrar una bolsa, solo se veía el contador; si la foto salió movida o era de otra bolsa, nadie se enteraba hasta la entrega.

## Alcance

Solo pantallas. Las fotos ya se guardan y ya se pueden ver con sus permisos (`/api/admin/foto` para el admin, el armador y atención, FA-01..FA-04); no cambia ninguna regla.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-336 | Al elegir una foto (entrega, entrega fallida, dañado o reclamo), se ve una miniatura antes de enviar, con la opción de cambiarla. La foto no sale del celular hasta tocar el botón de enviar. | — |
| S-337 | En cada tarjeta de armado se ven las miniaturas de las bolsas ya registradas, con su número; al tocar una se abre la foto completa. | — |

## Criterios de aceptación

- **VF-A · Vista previa al reclamar.** El vecino elige una foto en el reclamo → aparece su miniatura y el botón dice "Cambiar foto"; todavía no se llamó a la API. → S-336
- **VF-B · Vista previa en una foto del equipo.** En el formulario de foto (entrega, dañado), al elegir una foto aparece su miniatura antes de enviar. → S-336
- **VF-C · Bolsas registradas.** Un pedido con 2 bolsas muestra 2 miniaturas, cada una con el enlace a su foto (`/api/admin/foto?ruta=…`) y el texto "Bolsa 1" y "Bolsa 2". → S-337

## Trazabilidad

| Regla | Código | Pruebas |
|---|---|---|
| S-336 | `usePhotoPreview` y `PhotoPreview` en `PhotoForm.tsx` (enlace temporal que se libera al cambiar la foto o al salir); los usan `PhotoForm` y el reclamo de `OrdersPage.tsx` | `verFoto.test.ts` VF-A, VF-B |
| S-337 | `PackCard` en `AdminPanel.tsx`: lista `pack-bags` con `photoUrl` de cada bolsa | VF-C |

## Evidencia

- `66-web-rojo.txt`: las 3 pruebas fallan antes del código.
- `66-web-verde.txt`: TypeScript, 182 pruebas de la web y build en verde; el motor no cambia (733 pruebas en verde).
- Recorrido real en Chrome (demo local): la miniatura de la bolsa aparece al subirla y la del reclamo antes de enviarlo; 25 de 25 comprobaciones en verde.

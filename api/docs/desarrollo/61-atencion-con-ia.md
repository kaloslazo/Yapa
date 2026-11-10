# Iteración 61 · Ayuda de IA para atención: categoría, prioridad y borrador de respuesta

## Requisito

Como persona de atención, quiero que la IA me sugiera la categoría y la prioridad de un reclamo o una incidencia, y un borrador de respuesta para el vecino. Así atiendo más rápido, pero la decisión sigue siendo mía.

## Por qué

Kalos lo pidió el 09/11/2026, junto con "Arma mi canasta" (iteración 60), y usa los mismos proveedores (S-314). La IA **no aprueba, no rechaza ni cierra nada**: eso sigue en las reglas RV (reclamos) e IN (incidencias).

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-318 | Atención o el admin piden la sugerencia para un reclamo o una incidencia. Reciben una **categoría** (`FALTANTE`, `DANADO`, `ENTREGA`, `PAGO`, `TRATO`, `OTRO`), una **prioridad** (`ALTA`, `MEDIA`, `BAJA`) y un **borrador** de hasta 600 caracteres, en tono amable y sin prometer montos ni plazos. Al modelo se le manda el tipo, el producto y la cantidad, el motivo o la descripción y el estado del pedido. **Nunca** el nombre, el celular ni el correo. No cambia ningún estado. | — |
| S-319 | Si el modelo devuelve una categoría o una prioridad fuera de la lista, quedan `OTRO` y `MEDIA`. El borrador se recorta a 600 caracteres. Si no hay borrador → `IA_EMPTY_SUGGESTION`. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| IA-10 | Solo atención o el admin. | `NOT_AUTHORIZED` |
| IA-11 | El tipo es `reclamo` o `incidencia`, y el registro existe. | `INVALID_INPUT`, `CLAIM_NOT_FOUND`, `INCIDENT_NOT_FOUND` |
| IA-12 | Usa los proveedores de S-314 con el mismo respaldo. Si la IA está apagada o fallan los dos, responde con error. | `IA_DISABLED`, `IA_UNAVAILABLE` |
| IA-13 | La respuesta se limpia según S-319. No cambia el reclamo ni la incidencia. | `IA_EMPTY_SUGGESTION` |

## Criterios de aceptación

Modelo falso, sin internet.

- **IA-I · Reclamo.** Para un reclamo de 1 kg de cebolla `DANADO`, el modelo responde `{"categoria":"DANADO","prioridad":"ALTA","borrador":"Hola, sentimos que la cebolla llegó dañada…"}`. La sugerencia trae eso mismo y el reclamo sigue `PENDIENTE`. → IA-12, IA-13
- **IA-J · Valores fuera de lista.** Con `{"categoria":"QUEJA","prioridad":"URGENTE","borrador":"x"*700}` quedan `OTRO`, `MEDIA` y un borrador de 600 caracteres. → S-319
- **IA-K · Sin datos personales.** El mensaje al modelo no contiene el nombre, el celular ni el correo del vecino. → S-318
- **IA-L · Permisos y datos.** El armador → `NOT_AUTHORIZED`. Tipo `pedido` → `INVALID_INPUT`. Reclamo 999 → `CLAIM_NOT_FOUND`. Incidencia 999 → `INCIDENT_NOT_FOUND`. → IA-10, IA-11
- **IA-M · API.** `POST /api/admin/ia/atencion` con `{"tipo":"incidencia","id":1}` responde la sugerencia a atención y 403 al armador. → IA-10

## Trazabilidad

| Regla | Código | Pruebas (`tests/test_ia.py`) |
|---|---|---|
| IA-10, IA-11 | `ia.suggest_support` (`check_role` con `SUPPORT`) | `test_ia_l_roles_and_records`, `test_ia_api_basket_and_support` |
| IA-12, IA-13, S-319 | `ia.suggest_support` (lista de categorías y prioridades, recorte a 600) | `test_ia_i_*`, `test_ia_j_*` |
| S-318 | el caso no lleva nombre, celular ni correo | `test_ia_k_no_personal_data` |
| Web | `AiDraft` en `AdminPanel.tsx` (Reclamos e Incidencias) | revisión manual |

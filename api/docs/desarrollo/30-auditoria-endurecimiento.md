# Iteración 30 · Auditoría módulo por módulo y endurecimiento

## Requisito

Que ninguna entrada mal formada tumbe la API ni deje datos que rompan a los demás vecinos, y que el dinero siga cuadrando aunque el administrador toque pedidos cancelados.

## Origen

Auditoría del 17/10/2026 sobre todos los módulos del motor y la API. Se sondeó con entradas hostiles (tipos JSON equivocados, números enormes) y con una simulación de 600 semanas al azar (pedidos, ediciones, cancelaciones, retiros, entregas, fallas, reclamos y devoluciones), comprobando después de cada paso que la conciliación diera 0 y que ningún saldo quedara negativo. **El dinero resistió las 600 semanas.** Los huecos que aparecieron son los de abajo.

## Supuestos nuevos (a validar)

| # | Supuesto | Valor |
|---|---|---|
| S-170 | Una zona nueva necesita nombre. Sin nombre no se crea. | — |
| S-171 | En la API, un número que llega donde se espera texto (PIN, celular, código) se lee como su texto. Una lista o un objeto donde se espera un dato simple se rechaza. | — |

## Reglas

| Regla | Comportamiento | Error |
|---|---|---|
| AD-01 | Un pedido cancelado no admite verificar su pago: no entra plata a la caja de un pedido que ya no existe. | `ORDER_CANCELLED` |
| AD-02 | Crear una zona guarda las coordenadas como números, aunque lleguen como texto; y exige nombre (S-170). | `NAME_REQUIRED` |
| AD-03 | Una cantidad absurdamente grande (por ejemplo `1e999`) en un pedido, un reclamo o el colchón se rechaza con el error de cantidad, no con una caída. | `INVALID_QUANTITY`, `INVALID_CLAIM_ITEM` |
| AD-04 | La API lee los números como texto donde corresponde y rechaza listas y objetos sueltos (S-171). | `INVALID_INPUT` |
| AD-05 | Cualquier falla inesperada de la API responde JSON con estado 500 y el código `INTERNAL_ERROR`, nunca una página de texto. | `INTERNAL_ERROR` |
| AD-06 | Resumen, armado y métricas del admin validan que la semana exista (`2026-W99` no existe). | `INVALID_CYCLE` |

## Criterios de aceptación

- **AD-A · Verificar un cancelado.** El vecino 101 hace un pedido con Yape y lo cancela antes de que lo verifiquen. El admin intenta verificarlo → `ORDER_CANCELLED`; la caja sigue en 0 y la conciliación da diferencia 0. → AD-01
- **AD-B · Zona con coordenadas en texto.** Crear una zona con latitud `"-12.0690"` y longitud `"-77.0230"` deja `zone.lat` y `zone.lon` como números, y otro vecino cercano puede unirse sin error. Un nombre vacío → `NAME_REQUIRED`. → AD-02
- **AD-C · Cantidades enormes.** Pedir `1e999` kg de limón → `INVALID_QUANTITY`. Reclamar `1e999` → `INVALID_CLAIM_ITEM`. Meter `1e999` al colchón → `INVALID_QUANTITY`. → AD-03
- **AD-D · Entradas con tipo equivocado en la API.**
  - Entrar con `"secreto": 482915` (número) → entra, porque se lee `"482915"`.
  - Entrar con `"secreto": [1]` → 422 `INVALID_INPUT`.
  - Cambiar el PIN con `"nuevo": 135790` (número) → se cambia.
  - Publicar el catálogo con `"lista": 5` → 422 `INVALID_CATALOG_FORMAT`.
  - Alta de vecino con `"celular": 999888777` (número) → se da de alta.
  - Entrega fallida con `"motivo": ["x"]` → 422 `INVALID_INPUT`.
  → AD-04
- **AD-E · Falla inesperada.** Si un caso de uso lanza un error que no es de negocio, la API responde 500 con `{"error": {"codigo": "INTERNAL_ERROR", ...}}` y el servidor sigue atendiendo. → AD-05
- **AD-F · Semana inexistente.** `GET /api/admin/resumen?ciclo=2026-W99` y `ciclo=2026-W00` → 422 `INVALID_CYCLE`. → AD-06

## Hallazgos que no se corrigen aquí (para que el equipo decida)

- **Pago externo de un pedido cancelado sin verificar (S-20).** Si el vecino ya yapeó pero el admin no alcanzó a verificar antes de que cancelara, el sistema no devuelve nada. Con AD-01 el admin ya no puede "tapar" el caso verificando; hay que decidir cómo se devuelve esa plata (propuesta: el admin la registra a mano como devolución pendiente).
- **Sesiones de la API sin límite.** Se guardan en memoria y solo se borran al volver a usarlas o al cerrar sesión. Para el piloto no importa; con tráfico real hay que limpiarlas.
- **Cookie sin `Secure`.** Correcto en local por HTTP; al publicar con HTTPS hay que agregarlo.
- **Bloqueo por fuerza bruta.** Cinco fallos bloquean la cuenta 15 minutos (S-68): cualquiera puede bloquear la cuenta de un vecino a propósito. Es la decisión conocida; si molesta, bloquear por origen además de por cuenta.
- **Catálogo con más de 28 dígitos** en el máximo o el paso: solo lo publica el admin; no se cubre.

## Trazabilidad

| Regla | Código | Prueba |
|---|---|---|
| AD-01 | `order_registration.verify_payment` | `test_audit_hardening.test_ad_a_*` |
| AD-02, S-170 | `zones.create_zone` | `test_ad_b_*` |
| AD-03 | `domain.is_multiple`, `order_registration._check_quantity`, `claims._claim_quantity`, `buffer._quantity` | `test_ad_c_*` |
| AD-04, S-171 | `web/api._scalars` (en `_body`) | `test_api_hardening.test_ad_d_*` |
| AD-05 | `web/api.app` | `test_ad_e_*` |
| AD-06 | `web/api.query_cycle` | `test_ad_f_*` |

# Instrucciones para trabajar en este repo (Yapa)

Proyecto académico de Diseño de Software (UTEC 2026-2): Yapa, compras grupales semanales de vecinos en Lince, Jesús María y La Victoria. Metodología: **Specification-Driven Development (SDD)**.

## Antes de tocar código, leer en este orden

1. `docs/sdd/10-clarificaciones-v2.md`: decisiones del equipo (C-01..C-12) y supuestos (S-01..S-12).
2. `docs/desarrollo/00-roadmap.md`: iteraciones planificadas y estado.
3. `docs/desarrollo/99-registro.md`: qué se hizo en cada iteración.
4. La spec de la iteración en curso (`docs/desarrollo/NN-*.md`).

## Método obligatorio (cada iteración, commits en este orden)

1. `docs:` especificación: requisito, reglas con código de error, criterios de aceptación con números concretos, y supuestos nuevos numerados (S-38 en adelante) **marcados "a validar por el equipo"**.
2. `test:` pruebas de aceptación antes del código. Guardar la ejecución en rojo en `docs/evidencia/desarrollo/NN-*-rojo.txt`.
3. `feat:` implementación mínima que cumple la spec.
4. `docs:` trazabilidad (regla → código → prueba) en la misma spec, registro en `99-registro.md` y evidencia en verde.

Si durante la implementación aparece un caso que la spec no cubre, **primero** se actualiza la spec (`docs:`), luego la prueba (`test:`) y recién después el código.

## Reglas del proyecto

- **No inventar reglas de negocio.** Todo lo que no esté decidido va como supuesto numerado, para que el equipo lo valide.
- Nunca cobrar más de lo que el cliente vio (C-01, Ley 29571). El ahorro vuelve como saldo ("te devolvemos").
- Pruebas: verifican el **código de error** (`BusinessRuleError.code`), no el mensaje. Nombres `test_<criterio>_<descripción>`.
- **Las pruebas no se debilitan para que pasen.** Si una falla, se corrige el código o se discute la spec.
- Python 3.11+, solo biblioteca estándar. Estilo simple, como el código existente; sin sobre-ingeniería.
- Documentación en español, sin códigos crípticos en los textos para el usuario.
- Los commits **no** llevan línea de coautor de Claude ni "Generated with Claude Code" (pedido explícito del dueño del repo).

## Comandos

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m yapa_sdd.cli ciclo ejemplos/ciclo_demo.json
```

## Estado al 10/11/2026

- Iteraciones 2 a 48 y 50 a 62 **completas y en verde** (698 pruebas del motor, 152 del frontend); la 49 está reservada. El frontend React vive en `../src` (repo `kaloslazo/Yapa`) y usa la API de `src/yapa_sdd/web/api.py`. Ver `docs/desarrollo/00-roadmap.md` y `99-registro.md`.
- Iteración 63 validada localmente (11/11/2026), pendiente de revisión: `docs/desarrollo/63-paneles-y-explorar.md`; 718 pruebas del motor y 169 del frontend aprobadas, TypeScript y build. Compras y Reparto conservados.
- Iteración 64 (12/11/2026): la operación en el celular, `docs/desarrollo/64-operacion-en-el-celular.md`; 731 pruebas del motor y 176 de la web.
- Iteración 65 (12/11/2026): pedidos y reclamos del vecino como un carrito, `docs/desarrollo/65-reclamos-como-un-carrito.md`; 733 pruebas del motor y 179 de la web.
- Iteración 66 (12/11/2026): ver la foto que se toma, `docs/desarrollo/66-ver-la-foto.md`; 182 pruebas de la web.
- Iteración 67 (12/11/2026): cantidades con su unidad, `docs/desarrollo/67-cantidades-con-unidad.md`; 736 pruebas del motor y 185 de la web.
- Iteración 68 (16/11/2026): predicción de demanda, `docs/desarrollo/68-prediccion-de-demanda.md`.
- Iteración 69 (16/11/2026): la cotización del proveedor leída con IA, `docs/desarrollo/69-lista-del-proveedor-con-ia.md` (`quote_reader.py`; `ask_json` acepta imagen).
- Iteración 70 (16/11/2026): asistente de compra, `docs/desarrollo/70-asistente-de-compra.md` (`assistant.py`).
- Iteraciones 71 a 74 (17/11/2026, Aaron): revisión por bolsa y baja de bolsas, stock del proveedor por cargas (`supplier_stock.py`), chat como conversación y recorrido por calles (`street_routing.py`, OSRM de demostración: no apto para producción). Specs reescritas el 18/11 con el formato de las demás.
- Iteración 75: la antigua "64" de Aaron (`75-bolsas-con-selector.md`), renumerada el 18/11 porque repetía número y supuestos de la 64; su selector está retirado.
- Iteración 76 (18/11/2026): la bolsa se guarda con la foto (S-331) y el detector se usa a pedido y filtrado por pedido, `docs/desarrollo/76-bolsa-con-un-toque-y-detector-a-pedido.md` (`fulfillment.review_bag`, `POST /api/admin/bolsas/revision`).
- Iteración 77 (18/11/2026): la revisión de la bolsa la hace la IA con la lista del pedido y YOLO queda de respaldo, `docs/desarrollo/77-revision-de-bolsas-con-ia.md` (`bag_reader.py`; banco de fotos en `tools/banco_bolsas.py`).
- Iteración 78 (18/11/2026): las fotos se leen primero con Bedrock de la cuenta estudiantil UTEC (`bedrock.py`: Converse con firma SigV4 propia, sin dependencias), `docs/desarrollo/78-fotos-con-bedrock.md`. Variables `YAPA_BEDROCK_*`, nunca `AWS_*`; las pruebas reemplazan el envío y no salen a internet.
- Antes de numerar una iteración o un supuesto, mirar `main` actualizado: la 64 y S-327/S-328 se repitieron porque dos ramas tomaron el mismo número el mismo día.
- Supuestos usados: S-01..S-52, S-60..S-80, S-90..S-386. **El siguiente libre es S-387.**
- **Decisiones urgentes pendientes del equipo** al inicio de `docs/desarrollo/supuestos-a-validar.md`. El margen ya se lee con los costos reales (iteración 58: Plin al 0 % y flete propio); la parte del ahorro es 25 % (iteración 57). El simulador (`python -m yapa_sdd.simulator 40`) da los números.
- `close_cycle` es la forma operativa de liquidar (exige zonas entregadas o fallidas, suma los faltantes de compra y dañados, y retiene el 25 % del ahorro, S-301). `settle_cycle` es el cálculo puro que usan las pruebas y el simulador (0 % por defecto).
- Desde la iteración 56 una zona no se entrega sin la compra real registrada (S-299); en las pruebas, `buy_all` de `test_settlement.py`.
- IA (iteraciones 60 y 61, `ia.py`): Groq y, de respaldo, GitHub Models; se activa con `YAPA_GROQ_CLAVE` y/o `YAPA_GITHUB_MODELS_CLAVE`. Las pruebas usan un proveedor falso (`tests/test_ia.py`): nunca salen a internet.
- `audit.money_balance` debe dar diferencia 0. Toda iteración que mueva dinero debe mantenerlo (ver `test_e2e_week`).
- Tarea de campo pendiente: precios del mercado de barrio (`docs/desarrollo/kit-validacion-campo.md`).

## Levantar la web de demo

```bash
PYTHONPATH=src python -m yapa_sdd.web --demo   # semana ya vivida, en memoria (iteración 25)
PYTHONPATH=src python -m yapa_sdd.web --base yapa.db --ahora 2026-09-16T10:00:00-05:00
# credenciales de demo (solo con --demo o sin --base): se imprimen al arrancar (vecinos 101 y 105, admin admin-yapa, transportista reparto-demo, proveedor frescos-demo, y desde la iteración 55 compras-demo, armado-demo, atencion-demo y porteria-demo de Z-LINCE-01)
# vecinos nuevos: /admin/vecinos (el PIN se muestra una sola vez)
```

Modo servidor (iteración 44, ver `docs/desarrollo/44-produccion.md`): `--base` sin `--demo` no crea credenciales de demo; el administrador sale de `YAPA_ADMIN_USUARIO` y `YAPA_ADMIN_CLAVE`; `--escuchar 0.0.0.0` exige `--base`; `--estaticos ../dist` sirve la web construida; `GET /salud` para el chequeo.

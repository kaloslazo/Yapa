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

## Estado al 24/09/2026

- Iteraciones 2 (Lab 4), 3 (billetera), 4 (cancelar/editar) y 5 (zonas): **completas y en verde**.
- **Iteración 6 (catálogo semanal): spec y pruebas commiteadas, EN ROJO (9 errores esperados).** Falta:
  - crear `src/yapa_sdd/catalog.py` con `publish_catalog(store, cycle, products, *, by, now)` y `deactivate_product(store, cycle, product_id, *, by)`;
  - que `store` tenga `catalogs`, `admins` (con `"admin-yapa"` en el seed) y `suppliers` (seed: `SUP-FRESCOS` y `SUP-LIMPIEZA` aliados, `SUP-OTRO` no aliado);
  - `Product.supplier_id` opcional;
  - reservas por ciclo: `reserve(product_id, qty, cycle)`, `reserved_quantity(product_id, cycle)`, `release(product_id, qty, cycle)`;
  - `quote_order(store, lines, cycle=None)` que use `store.catalog_for(cycle)`;
  - registro, edición, cancelación y liquidación con el catálogo y las reservas del ciclo del pedido.

  Ver `docs/desarrollo/06-catalogo-semanal.md` y `tests/test_catalog.py`.
- Pendientes después: iteración 7 (armado con foto por bolsa, entrega en portería con foto, reclamo por artículo en 24 h, colchón de reposición con tope) e iteración 8 (métricas: recompra en la semana 4, margen por pedido, ahorro entregado). Ver `docs/desarrollo/00-roadmap.md` y `docs/analisis/07_modelo_precios_zonas.md`.

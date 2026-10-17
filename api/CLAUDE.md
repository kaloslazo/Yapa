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

## Estado al 17/10/2026

- Iteraciones 2 a 27 **completas y en verde** (314 pruebas). El frontend React vive en `../src` (repo `kaloslazo/Yapa`) y usa la API de `src/yapa_sdd/web/api.py`. Ver `docs/desarrollo/00-roadmap.md` y `99-registro.md`.
- Supuestos usados: S-01..S-52, S-60..S-80, S-90..S-157. **El siguiente libre es S-158.**
- **Decisiones urgentes pendientes del equipo** al inicio de `docs/desarrollo/supuestos-a-validar.md`. Las más importantes son el margen (optimista vs. pesimista) y si Yapa retiene parte del ahorro. El simulador (`python -m yapa_sdd.simulator 40`) da los números.
- `close_cycle` es la forma operativa de liquidar (exige zonas entregadas o fallidas). `settle_cycle` es el cálculo puro que usan las pruebas y el simulador.
- `audit.money_balance` debe dar diferencia 0. Toda iteración que mueva dinero debe mantenerlo (ver `test_e2e_week`).
- Tarea de campo pendiente: precios del mercado de barrio (`docs/desarrollo/kit-validacion-campo.md`).

## Levantar la web de demo

```bash
PYTHONPATH=src python -m yapa_sdd.web --demo   # semana ya vivida, en memoria (iteración 25)
PYTHONPATH=src python -m yapa_sdd.web --base yapa.db --ahora 2026-09-16T10:00:00-05:00
# credenciales de demo: se imprimen al arrancar (vecinos 101 y 105, admin admin-yapa)
# vecinos nuevos: /admin/vecinos (el PIN se muestra una sola vez)
```

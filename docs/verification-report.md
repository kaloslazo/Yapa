# Informe de verificación SDD Yapa

Fecha: 19 de septiembre de 2026.

## Código

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Resultado esperado: suite de validaciones de CUN-02 correcta.

## Presentación

- 12 diapositivas.
- Alcance centrado en SDD y Yapa.
- Estilo visual minimalista en blanco, negro y grises, con tipografía Helvetica Neue.
- Texto editable y notas del orador con fuentes.
- Validación estructural del paquete correcta.
- Render de las 12 diapositivas revisado.

## Comparación con el markdown del curso

| Requisito de la sección SDD | Evidencia en la entrega |
|---|---|
| Explicar qué es SDD y su objetivo | `docs/02-metodologia-sdd.md` y diapositivas 2–4 |
| Explicar el problema que busca resolver | Ambigüedad, cambios, documentación desactualizada y comunicación entre roles |
| Requisitos y especificaciones | `docs/sdd/02-especificacion-cun-02.md` y diapositiva 6 |
| Reglas de negocio | RN-01, RN-02, RN-03, RN-04, RN-05, RN-07, RN-09 y RN-10 |
| Criterios de aceptación | `docs/sdd/05-criterios-aceptacion.md` y diapositiva 7 |
| Contrato de entrada y salida | Entrada y salida de CUN-02 en la diapositiva 6 |
| Modelo o diagrama de diseño | Modelo mínimo de dominio en la diapositiva 8 |
| Ventajas y limitaciones | Diapositiva 11 y `docs/05-resultados-sdd-yapa.md` |
| Herramientas | Markdown, GitHub, Python, unittest y agentes de IA en la diapositiva 9 |
| Aplicación sobre un proyecto real | Yapa, CUN-02 Registrar pedido semanal |
| Código funcional y demostración | `src/yapa_sdd/order_registration.py` y ejecución de la suite |
| Validación contra la especificación | 8 tests correctos y matriz en `docs/sdd/06-trazabilidad.md` |

## Alcance y límite

La entrega cumple la parte SDD asignada al Grupo 1 y 3. El material de TDD del documento académico no se presenta porque pertenece a los Grupos 2 y 4. La demostración es un módulo de dominio ejecutable, no una aplicación web completa; persistencia, interfaz, pagos externos, mapas y CUN-03 completo quedan en el roadmap general de Yapa.

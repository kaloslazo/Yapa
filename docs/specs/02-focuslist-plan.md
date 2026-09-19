# Plan técnico de FocusList v1

## Decisiones

- **Lenguaje**: Python 3.11+.
- **Interfaz**: `argparse` con subcomandos `add`, `list` y `done`.
- **Persistencia**: `pathlib.Path` + `json` en un archivo local.
- **Dominio**: funciones pequeñas (`add_task`, `list_tasks`, `complete_task`) separadas de la CLI.
- **Pruebas**: `unittest` y directorio temporal por test.
- **Integridad de escritura**: escribir `.tmp` y reemplazar el destino.

## Estructura

```text
src/focuslist/cli.py   # dominio y CLI
tests/test_focuslist.py
docs/specs/*.md
```

## Mapeo de reglas a implementación

| Regla | Diseño |
| --- | --- |
| Título recortado y limitado | `add_task` valida antes de persistir |
| IDs incrementales | `next_id` en el JSON |
| Filtros | `list_tasks(store, status)` |
| Idempotencia | `complete_task` devuelve si hubo cambio |
| Archivo corrupto | convertir `JSONDecodeError` en `FocusListError` |
| CLI sin traceback | `main` traduce `FocusListError` a código 2 |

## Estrategia de verificación

Cada criterio de aceptación tendrá al menos una prueba. Además, se verificará que el archivo JSON se pueda leer y que el ejemplo de comandos del README funcione.


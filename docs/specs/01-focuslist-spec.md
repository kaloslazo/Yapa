# Especificación de FocusList v1

## Objetivo

Una persona necesita gestionar una lista local de tareas desde la terminal, sin depender de un servicio externo.

## Alcance

La aplicación permite crear tareas, listar tareas y marcar una tarea como completada. La información vive en un archivo JSON local.

## Historias y criterios de aceptación

### US-01 Crear tarea

Como persona usuaria, quiero crear una tarea con un título para recordar trabajo pendiente.

- **AC-01.1**: Cuando se recibe un título con espacios al principio o al final, el sistema guarda el título recortado.
- **AC-01.2**: Cuando el título queda vacío después de recortarlo, el sistema rechaza la operación con un error legible.
- **AC-01.3**: Cuando el título supera 80 caracteres, el sistema rechaza la operación con un error legible.
- **AC-01.4**: Cuando se crea una tarea válida, el sistema asigna un ID entero incremental y la marca como abierta.

### US-02 Listar tareas

Como persona usuaria, quiero ver mis tareas ordenadas por ID.

- **AC-02.1**: El listado muestra ID, título y estado.
- **AC-02.2**: `all` devuelve todas las tareas.
- **AC-02.3**: `open` devuelve solo tareas no completadas.
- **AC-02.4**: `done` devuelve solo tareas completadas.
- **AC-02.5**: Si no hay resultados, el sistema muestra `No hay tareas.`.

### US-03 Completar tarea

Como persona usuaria, quiero marcar una tarea como completada.

- **AC-03.1**: Cuando el ID existe y la tarea está abierta, el sistema la marca como completada y persiste el cambio.
- **AC-03.2**: Cuando el ID ya está completado, repetir la operación no cambia los datos y devuelve un mensaje informativo.
- **AC-03.3**: Cuando el ID no existe, el sistema rechaza la operación con un error legible.

## Persistencia

El archivo contiene `next_id` y una lista `tasks`. Cada tarea contiene `id`, `title`, `done` y `created_at`. Las escrituras reemplazan el archivo mediante un temporal para evitar dejar un archivo parcialmente escrito.

## No funcionales

- Python 3.11 o superior.
- Sin dependencias externas en tiempo de ejecución.
- UTF-8 y JSON legible para humanos.
- Las funciones de dominio deben poder probarse sin invocar la CLI.

## Preguntas resueltas

- ID: entero incremental local.
- Estado: abierta o completada.
- Repetir `done`: idempotente.
- Eliminación: fuera de alcance de v1.
- Archivo: `FOCUSLIST_DB`, `--store` o `.focuslist.json` por defecto.


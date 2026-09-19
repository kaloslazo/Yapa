# Cómo aplicaría SDD y TDD en un trabajo real

## Respuesta corta para la clase

Aplicaría SDD para definir el comportamiento antes de escribir código y TDD para implementar cada criterio de aceptación de forma incremental. La spec evita que la IA o el equipo inventen reglas; TDD comprueba esas reglas en ciclos pequeños.

## Flujo de trabajo

```text
necesidad del usuario
        ↓
spec con escenarios y aceptación
        ↓
plan técnico y tareas
        ↓
test que falla
        ↓
código mínimo
        ↓
test verde y refactor
        ↓
convergencia contra la spec
```

## Ejemplo aplicado a FocusList

### Criterio de aceptación

Cuando la persona marca una tarea abierta como completada, el sistema debe persistir `done = true`. Si repite la operación, no debe crear otro cambio ni fallar.

### Primero el test

```python
def test_done_is_idempotent(self):
    task = add_task("Revisar", self.store)
    _, first_change = complete_task(task.id, self.store)
    _, second_change = complete_task(task.id, self.store)
    self.assertTrue(first_change)
    self.assertFalse(second_change)
```

### Implementación mínima

```python
if task.done:
    return task, False
task.done = True
save_tasks(store, next_id, tasks)
return task, True
```

La spec define el comportamiento idempotente; TDD obliga a demostrarlo con una prueba de regresión. La IA puede proponer el test y la implementación, pero la persona revisa que el criterio represente la intención real.

## Puntos clave para manejar la metodología

- Mantener la spec corta, específica y versionada.
- No pasar a plan o código con preguntas de negocio abiertas.
- Relacionar cada criterio con una tarea y una prueba.
- Pedir a la IA un cambio pequeño por iteración.
- Revisar el diff, no solo el resultado final.
- Ejecutar tests unitarios, de integración y de contrato cuando el riesgo lo pida.
- Registrar supuestos, decisiones y trabajo pendiente.
- Actualizar la spec cuando el producto cambie.
- Evitar cargar instrucciones que nadie puede mantener.

## Cómo explicaría si “funcionó”

En el ejemplo funcionó para reducir ambigüedad, descubrir el caso de doble `done` y mantener la relación entre requisito, test y código. Todavía no demuestra productividad superior ni calidad de producción. Para afirmarlo haría falta comparar el mismo cambio con un flujo sin SDD/TDD y medir retrabajo, defectos y tiempo.


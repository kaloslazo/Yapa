# Constitución de FocusList

## Principios

1. **Comportamiento explícito**: toda regla observable debe aparecer en la spec y en una prueba.
2. **Simplicidad**: usar Python 3.11 y biblioteca estándar; no introducir dependencias para una demo local.
3. **Persistencia legible**: guardar JSON UTF-8 para facilitar inspección y aprendizaje.
4. **Cambios trazables**: modificar spec, plan, tareas, código y pruebas en ese orden cuando cambie una regla.
5. **Errores útiles**: mostrar mensajes breves, claros y sin traceback a la persona usuaria.
6. **Revisión humana**: la IA puede proponer y ejecutar cambios, pero una persona aprueba alcance, riesgos y aceptación.

## Fuera de alcance

Red, interfaz gráfica, autenticación, sincronización entre usuarios, concurrencia, backup, migraciones y despliegue.


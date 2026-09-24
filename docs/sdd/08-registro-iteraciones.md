# Registro de iteraciones SDD

## Iteración 0 · contexto

Se tomó el modelado de negocio de Yapa como fuente. Se identificó que una implementación completa de CUN-01 a CUN-08 desviaría la entrega de la demostración de SDD.

## Iteración 1 · alcance

Se seleccionó CUN-02 Registrar pedido semanal y el contrato mínimo de CUN-03. Se declararon como diferidos peso real, sustituciones, conciliación, consolidación, abastecimiento, preparación, reparto e incidencias.

## Iteración 2 · especificación

Se derivaron ocho reglas implementables y seis criterios de aceptación. También se fijaron errores observables y la salida `REGISTRADO`.

## Iteración 3 · plan e implementación

Se eligió un módulo de dominio sin infraestructura. Cada tarea del plan se enlazó con una regla y una prueba.

## Iteración 4 · convergencia

La suite confirma la vertical elegida. Las reglas diferidas no aparecen como funcionalidades terminadas y quedan en el repositorio general como trabajo futuro.


## Iteración 5 · revisión crítica (23/09/2026)

Se contrastó la spec con el código (14 discordancias reproducibles), con la idea inicial y los antecedentes (Favo, Muni, Merqueo...) y con la ley (Ley 29571). El cobro de saldo en la puerta (RN-21) resultó ilegal y el modelo repetía el patrón de Favo. Ver `docs/analisis/`.

## Iteración 6 · validación económica (24/09/2026)

Con precios reales se vio que los abarrotes de marca solo tienen una brecha de 6.5 % frente al supermercado, así que el margen no alcanza. En frescos resistentes la brecha es de 36–67 %. Se redefinió el catálogo piloto.

## Iteración 7 · clarificación y spec v2 (24/09/2026)

Decisiones C-01..C-12 y supuestos S-01..S-12. Se reescribió la spec de registro (RP-01..RP-15) y se creó la de liquidación (LQ-01..LQ-09). Se escribieron 24 criterios de aceptación.

## Iteración 8 · pruebas, implementación y convergencia (24/09/2026)

- Las pruebas se escribieron antes que el código: la evidencia en rojo está en `docs/evidencia/01`.
- Se implementó por capas: dominio, ciclo, repositorio, casos de uso y consola.
- Durante la implementación salieron dos ajustes de spec (la cotización y el faltante en un pedido no entregado). Ambos entraron primero como docs y tests.
- La revisión de casos borde encontró tres fallos: una cantidad NaN o infinita, un monto no numérico, y un tramo que no empieza en 0. Se agregaron sus pruebas y se corrigieron.
- Resultado: 45 pruebas en verde y la demo en consola funcionando.

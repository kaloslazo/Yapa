# Iteración 49 · Despliegue automático

## Requisito

Como equipo (Carlos y Kalos), queremos que cuando se suba código a `main` se corran las pruebas, se construya la web y se actualice `holayapa.app` solo, sin que nadie tenga que entrar a la VPS, y que si una versión sale mala la web siga funcionando con la anterior.

## Por qué

Hoy cada cambio se sube a mano: se arma el paquete, se copia a la VPS y se reinicia el motor. Funciona, pero depende de una persona con la VPN conectada. Kalos propuso un runner de GitHub en la VPS manteniendo Caddy y Cloudflare. Se comprobó el 21/10 que el runner sí arranca en Windows Server 2012 R2 y que Node 20 corre ahí; Node 24 no, así que el trabajo de la VPS usa solo comandos de PowerShell y ninguna acción de GitHub hecha con Node.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-259 | **Solo `main` despliega.** Cada subida a cualquier rama corre las pruebas y construye el paquete; **solo una subida a `main`** (no un pull request ni otra rama) lo despliega. | `main` |
| S-260 | **Las pruebas mandan**: el despliegue no empieza si fallan las pruebas del motor (557), las de la web (93), el chequeo de tipos o la compilación. | pruebas antes |
| S-261 | **El paquete se construye en los servidores de GitHub** (no en la VPS, que no tiene Node) y la VPS lo descarga con un **token temporal** que GitHub crea para cada ejecución, limitado a este repositorio y que caduca al terminar. En la VPS no se guarda ninguna credencial de GitHub salvo la del propio runner, que solo sirve para recibir trabajos de este repo. | token temporal |
| S-262 | **El script de despliegue vive en la VPS** (`C:\yapa\ci\desplegar-ci.ps1`), no en el repositorio: el flujo de trabajo solo lo llama. Una copia de referencia está en `deploy/vps/` para que se pueda revisar. | script en la VPS |
| S-263 | **Respaldo y marcha atrás**: antes de cambiar nada se respalda la base; la versión anterior se guarda; si la nueva no responde `GET /salud` en 40 segundos, se vuelve a la anterior y el trabajo falla. Los datos (la base) nunca se tocan. | vuelve a la anterior |
| S-264 | **El runner corre como programa normal, sin servicio de Windows**, con el mismo usuario que el motor; no arranca solo si la VPS se reinicia (no se espera que pase). Solo recibe trabajos con la etiqueta `yapa-vps`. | sin servicio |
| S-265 | **Un despliegue a la vez**: si llegan dos subidas seguidas, el segundo espera al primero. | en fila |

## Reglas

| Regla | Comportamiento |
|---|---|
| DA-01 | El flujo de trabajo corre en cada subida a cualquier rama y en cada pull request hacia `main`: pruebas del motor, tipos, pruebas de la web y compilación. |
| DA-02 | El paquete (`api/src` y `dist`, sin `__pycache__`) se guarda como artefacto de esa ejecución con la misma forma que el paquete manual, para usar el mismo despliegue. |
| DA-03 | El trabajo de despliegue solo existe para una subida (`push`) a `refs/heads/main` y solo después de que pasaron las pruebas. Corre en el runner de la VPS con la etiqueta `yapa-vps`, en una fila (S-265). |
| DA-04 | `desplegar-ci.ps1` descarga el artefacto de esa ejecución, respalda la base, para el motor, guarda la versión anterior, pone la nueva y arranca el motor. |
| DA-05 | Si `GET /salud` no responde bien en 40 segundos, restaura la versión anterior, la arranca y termina con error. Si la nueva responde, el despliegue termina bien. |
| DA-06 | Un paquete vacío, incompleto o sin la web (`dist/index.html`) o sin el motor se rechaza antes de tocar la versión que corre. |
| DA-07 | Cada despliegue deja una línea en `C:\yapa\ci\despliegues.log` con hora, ejecución y resultado. |

## Criterios de aceptación

| # | Criterio | Cómo se comprueba | Resultado |
|---|---|---|---|
| DA-A | El flujo de trabajo es válido | `actionlint` sobre `.github/workflows/ci.yml` | sin errores |
| DA-B | Las pruebas corren limpias en Linux, como en GitHub | el mismo comando del flujo en una máquina Linux (o la primera ejecución en GitHub) | 557 del motor y 93 de la web en verde |
| DA-C | Despliegue normal | `desplegar-ci.ps1 -ZipLocal` en la VPS con el paquete bueno | `GET /salud` bien, versión nueva activa, `despliegues.log` con "ok" |
| DA-D | Marcha atrás | el mismo script con un paquete cuyo motor no arranca | termina con error, la versión anterior vuelve a responder, la base intacta, el registro dice "restaurado" |
| DA-E | Paquete inválido | un zip vacío o sin `dist/index.html` | se rechaza, la versión que corre ni se detiene |
| DA-F | Bajada desde GitHub | la función de descarga contra un artefacto real de una ejecución | el zip baja completo (sigue la redirección sin mandar el token al sitio de descarga) |
| DA-G | Solo `main` despliega | revisión del flujo | el trabajo de despliegue tiene la condición de `push` y `main` |
| DA-H | Todo en conjunto | una subida real a `main` con el runner registrado | la web cambia sola y `/salud` sigue bien |

DA-H necesita que Kalos registre el runner y que se suba a `main`; se prueba cuando eso ocurra.

## Fuera de esta iteración (anotado)

- Correr el runner con un usuario sin permisos de administrador (hoy comparte el del motor).
- Que la VPS se reinicie sola con el motor, el túnel y el runner, que necesita una tarea de arranque en el servidor del tío de Carlos.
- **Registro abierto con ubicación y aprobación del admin de zona**: pasa a la iteración 50.

# Iteración 52 · Despliegue automático

## Requisito

Como equipo (Carlos y Kalos), queremos que cuando se suba código a `main` se corran las pruebas, se construya la web y se actualice `holayapa.app` solo, sin que nadie tenga que entrar a la VPS, y que si una versión sale mala la web siga funcionando con la anterior.

## Por qué

Hoy cada cambio se sube a mano: se arma el paquete, se copia a la VPS y se reinicia el motor. Funciona, pero depende de una persona con la VPN conectada. Kalos propuso un runner de GitHub en la VPS manteniendo Caddy y Cloudflare. Se comprobó el 21/10 que el runner sí arranca en Windows Server 2012 R2 y que Node 20 corre ahí; Node 24 no, así que el trabajo de la VPS usa solo comandos de PowerShell y ninguna acción de GitHub hecha con Node.

## Supuestos nuevos (a validar por el equipo)

| # | Supuesto | Valor |
|---|---|---|
| S-270 | **Solo `main` despliega.** Cada subida a cualquier rama corre las pruebas y construye el paquete; **solo una subida a `main`** (no un pull request ni otra rama) lo despliega. | `main` |
| S-271 | **Las pruebas mandan**: el despliegue no empieza si fallan las pruebas del motor (557), las de la web (93), el chequeo de tipos o la compilación. | pruebas antes |
| S-272 | **El paquete se construye en los servidores de GitHub** (no en la VPS, que no tiene Node) y la VPS lo descarga con un **token temporal** que GitHub crea para cada ejecución, limitado a este repositorio y que caduca al terminar. En la VPS no se guarda ninguna credencial de GitHub salvo la del propio runner, que solo sirve para recibir trabajos de este repo. | token temporal |
| S-273 | **El script de despliegue vive en la VPS** (`C:\yapa\ci\desplegar-ci.ps1`), no en el repositorio: el flujo de trabajo solo lo llama. Una copia de referencia está en `deploy/vps/` para que se pueda revisar. | script en la VPS |
| S-274 | **Respaldo y marcha atrás**: antes de cambiar nada se respalda la base; la versión anterior se guarda; si la nueva no responde `GET /salud` en 40 segundos, se vuelve a la anterior y el trabajo falla. Los datos (la base) nunca se tocan. | vuelve a la anterior |
| S-275 | **El runner corre como programa normal, sin servicio de Windows**, con el mismo usuario que el motor; no arranca solo si la VPS se reinicia (no se espera que pase). Solo recibe trabajos con la etiqueta `yapa-vps`. | sin servicio |
| S-276 | **Un despliegue a la vez**: si llegan dos subidas seguidas, el segundo espera al primero. | en fila |

## Reglas

| Regla | Comportamiento |
|---|---|
| DA-01 | El flujo de trabajo corre en cada subida a cualquier rama y en cada pull request hacia `main`: pruebas del motor, tipos, pruebas de la web y compilación. |
| DA-02 | El paquete (`api/src` y `dist`, sin `__pycache__`) se guarda como artefacto de esa ejecución con la misma forma que el paquete manual, para usar el mismo despliegue. |
| DA-03 | El trabajo de despliegue solo existe para una subida (`push`) a `refs/heads/main` y solo después de que pasaron las pruebas. Corre en el runner de la VPS con la etiqueta `yapa-vps`, en una fila (S-276). |
| DA-04 | `desplegar-ci.ps1` descarga el artefacto de esa ejecución, respalda la base, para el motor, guarda la versión anterior, pone la nueva y arranca el motor. |
| DA-05 | Si `GET /salud` no responde bien en 40 segundos, restaura la versión anterior, la arranca y termina con error. Si la nueva responde, el despliegue termina bien. |
| DA-06 | Un paquete vacío, incompleto o sin la web (`dist/index.html`) o sin el motor se rechaza antes de tocar la versión que corre. |
| DA-07 | Cada despliegue deja una línea en `C:\yapa\ci\despliegues.log` con hora, ejecución y resultado. |
| DA-08 | La página lleva, **sin mostrarse**, el código del commit desplegado (7 primeros caracteres de `GITHUB_SHA`; `local` fuera de GitHub) en `<meta name="yapa-build">`, para ver en producción si el despliegue cambió la versión (con ver código fuente o `curl`). En la primera prueba (21/10) estuvo visible en el pie; se ocultó una vez comprobado el despliegue. |

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
| DA-J | La versión va oculta | prueba de archivos de la web | la compilación pone `GITHUB_SHA` en el `<meta>` y la pantalla no la muestra |
| DA-H | Todo en conjunto | una subida real a `main` con el runner registrado | la web cambia sola, la página lleva el código del commit nuevo y `/salud` sigue bien |

DA-H se probó el 21/10: el runner se registró a las 19:26 y la prueba fue subir a `main` con la etiqueta de versión del pie (DA-08).

## Trazabilidad y resultados

| Regla / supuesto | Código | Prueba |
|---|---|---|
| DA-01, DA-02, S-271 | `.github/workflows/ci.yml`: trabajos `motor` y `web` (de Kalos) y, en `web`, el armado y la subida del paquete | DA-A, DA-B |
| DA-03, S-270, S-276 | trabajo `desplegar` con `if: push` a `refs/heads/main`, `needs: [motor, web]` y `concurrency` | DA-G |
| DA-04, S-272, S-273 | `deploy/vps/desplegar-ci.ps1` (copia de referencia; la que corre está en `C:\yapa\ci\`) | DA-C, DA-F |
| DA-05, S-274 | `Esta-Sano` (40 segundos de reloj) y `Restaurar` | DA-D |
| DA-06 | `Validar-Paquete` | DA-E |
| DA-07 | `Log` en `C:\yapa\ci\despliegues.log` | DA-C, DA-D |
| DA-08, DA-J | `vite.config.ts` (complemento `yapa-build`, `GITHUB_SHA`) | `scripts/publicAssets.test.ts` |
| S-275 | `deploy/vps/instalar-runner.ps1`, `iniciar-runner.ps1` (sin servicio de Windows) | DA-H (pendiente) |

Resultados (21/10/2026):

| # | Resultado |
|---|---|
| DA-A | `actionlint` sin errores sobre el flujo ya combinado con el de Kalos; se comprobó que el validador detecta errores reales (una propiedad mal escrita) |
| DA-B | La primera ejecución en GitHub pasó en Linux (`Pruebas y paquete`), y con el flujo integrado: 584 pruebas del motor y 99 de la web en verde, tipos y compilación sin errores |
| DA-C | En la VPS: versión nueva activa (otro proceso del motor), la anterior guardada en `app.prev`, base de 81 920 bytes intacta, respaldo hecho, `holayapa.app/salud` bien y Ana sigue entrando |
| DA-D | Con un motor roto: `FALLÓ`, `restaurado`, código de salida 1, base intacta, la web pública no dejó de responder. La primera vez tardó 84 s en rendirse (límite por intentos); se cambió a 40 s de reloj y repetida tardó 45 s |
| DA-E | Un paquete vacío y uno sin `dist/index.html` se rechazan con código 1 **sin detener el motor** (mismo proceso antes y después) |
| DA-F | Con la función real del script contra la ejecución real de GitHub: baja 765 KB, sigue la redirección sin mandar el token al almacén, y el paquete es válido |
| DA-G | En GitHub, en una rama, el trabajo `Desplegar en la VPS` se **saltó** (`skipped`) |
| DA-H | **Aprobado (21/10, 19:31)**: se subió a `main` (`7b1dead`); GitHub corrió `motor` y `web` y después `desplegar en la VPS` en el runner `vps-yapa`, que terminó en éxito en 12 s (19:31:20 a 19:31:32, según `despliegues.log`). En `holayapa.app` el archivo principal de la web pasó de `index-BVzhe2t8.js` a `index-BHVMNNAr.js`, el pie lleva la etiqueta `7b1dead`, `/salud` responde bien y las cuentas de demostración entran |
| DA-I | **El paquete que construyó GitHub se desplegó en la VPS** con el mismo script (`-ZipLocal`, paquete bajado de la ejecución 39696047470): versión de Kalos con sus cabeceras (CSP, HSTS), zonas públicas sin contacto, y las cuentas de demostración siguen entrando |

Hallazgos que cambiaron el trabajo:

- El Windows de la VPS lee los `.ps1` sin marca de codificación como ANSI y una "Ó" rompió una cadena; los scripts van guardados con BOM.
- GitHub ya tenía el flujo `tests` de Kalos en `main` en el mismo archivo `ci.yml`; se combinaron en uno solo sin tocar los nombres de sus trabajos (`motor`, `web`).
- La numeración se reordenó porque Kalos ya usaba S-259 a S-269 y las iteraciones 50 y 51: esta iteración es la **52** y sus supuestos van de S-270 a S-276; la 49 sigue reservada para el registro abierto.
- El endurecimiento de Kalos (iteración 51) calcula la dirección del cliente con `X-Forwarded-For` cuando la petición viene de la misma máquina. **Comprobado en producción con el túnel de Cloudflare (21/10):** 30 intentos fallidos desde mi PC (`45.236.45.62`) dieron 429 en el 31.º, también con el PIN bueno; en ese momento, desde la VPS (otra dirección pública, `181.224.242.173`) el ingreso de Carmen dio 200. Cada persona se ve con su propia dirección y el límite no bloquea a todos juntos.

## Fuera de esta iteración (anotado)

- Correr el runner con un usuario sin permisos de administrador (hoy comparte el del motor).
- Que la VPS se reinicie sola con el motor, el túnel y el runner, que necesita una tarea de arranque en el servidor del tío de Carlos.
- **Registro abierto con ubicación y aprobación del admin de zona**: es la iteración 49, reservada en la hoja de ruta.

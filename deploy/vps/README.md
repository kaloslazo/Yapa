# Despliegue automático en la VPS

Iteración 52 (`api/docs/desarrollo/52-despliegue-automatico.md`). Esta carpeta guarda **copias de referencia** de los scripts que corren en la VPS, para que se puedan revisar. Los que corren de verdad están en la VPS (`C:\yapa\ci\`), no en el repositorio: el flujo de GitHub solo los llama (S-273).

## Cómo funciona

1. Subes código a **`main`**. GitHub (en sus servidores) corre las pruebas del motor y de la web, el chequeo de tipos y la compilación, y arma el paquete (`api/src` y `dist`).
2. Si todo pasó, el trabajo **desplegar en la VPS** corre en el runner de la VPS (etiqueta `yapa-vps`): `C:\yapa\ci\desplegar-ci.ps1` baja el paquete con un token temporal de GitHub, respalda la base, guarda la versión anterior, pone la nueva y arranca el motor.
3. Si el motor nuevo no responde `/salud` en 40 segundos, vuelve a la versión anterior y el trabajo falla. La base nunca se toca.
4. Las ramas y los pull requests **solo corren las pruebas**, no despliegan.

Cada despliegue deja una línea en `C:\yapa\ci\despliegues.log` de la VPS.

## Registrar el runner (una sola vez; lo hace quien administra el repo)

1. En GitHub: el repositorio → **Settings → Actions → Runners → New self-hosted runner → Windows**.
2. En los comandos que aparecen, copia **el código del `--token`** (vale una hora). No lo publiques.
3. Pásaselo a quien tiene acceso a la VPS, que corre:
   ```
   C:\yapa\ci\instalar-runner.ps1 -Token <el código>
   ```
   Eso descarga el runner, lo registra con la etiqueta `yapa-vps` y lo deja corriendo.
4. En **Settings → Actions → Runners** el runner `vps-yapa` debe aparecer como **Idle** (verde).

Recomendado: en **Settings → Branches** proteger `main` (exigir que pasen `motor` y `web`), porque quien suba a `main` cambia la web real.

## Cosas que hay que saber

- El runner corre **como programa normal, sin servicio de Windows** (S-275): si la VPS se reinicia, hay que volver a lanzarlo con `C:\yapa\ci\iniciar-runner.ps1` (y el motor y el túnel de Cloudflare también).
- El Windows de la VPS (Server 2012 R2) **no corre Node 24**: por eso el trabajo de la VPS usa solo comandos de PowerShell y ninguna acción de GitHub. No agregues ahí acciones como `actions/checkout`.
- El runner ejecuta en esa máquina lo que diga `.github/workflows/ci.yml`: solo debe poder cambiarlo quien tiene permiso sobre el repositorio.
- Para volver a una versión anterior a mano: la anterior queda en `C:\yapa\app.prev` hasta el siguiente despliegue.

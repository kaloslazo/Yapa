# Validación local de pulir-detalles

Fecha: 14/11/2026. Carpeta: `Yapa-publicacion`. Rama: `pulir-detalles`.

## Base de trabajo

Se creó la rama desde `aaron/bolsas-por-foto` y se incorporó `origin/main` (`2d95212`) mediante el commit local de integración `895fdad`. Se conservaron las tarjetas móviles, las unidades y miniaturas del equipo. El selector de varias bolsas, con una foto por bolsa y confirmación, se ofrece dentro de «Preparar varias bolsas con fotos», junto a la cámara directa del equipo. Se conservaron ambos registros de desarrollo.

Los cuatro commits anteriores del selector de bolsas todavía no estaban en `origin/main`: también formarán parte de esta rama al subirla. Los cambios nuevos de avisos quedan pendientes de los seis commits indicados abajo. No se hizo push ni se modificó main.

## Resultado

- Seis pruebas nuevas del motor: antes del cambio, tres fallaban por los textos antiguos; las otras tres ya verificaban el comportamiento existente.
- Regresión del motor: 724 pruebas ejecutadas, 720 aprobadas y 4 omitidas en este entorno. Incluye las seis nuevas, la frontera exacta del cierre, las zonas pendientes y el cierre con entrega fallida registrada.
- Frontend: 190 pruebas aprobadas, en 30 archivos. Se precisó el selector de la prueba de cámara directa para distinguirla del formulario de varias fotos y se comprobó la ayuda del horario.
- `npm.cmd run typecheck`: aprobado.
- `npm.cmd run build`: aprobado. Vite mantiene un aviso por un chunk de más de 500 kB.
- Entorno usado: Node 24.20.0, npm 11.19.0 y Python 3.14.7. No equivale a una ejecución del CI, que utiliza Node 22 y Python 3.11. El motor emitió un ResourceWarning de conexión SQLite sin cerrar durante sus pruebas.
- No se hizo revisión visual en navegador para este ajuste de textos. No se cambiaron relojes, datos locales, fotos ni reglas de negocio.

## Seis commits y subida

Desde PowerShell, ejecutar en orden. Los primeros commits reflejan el orden especificación → pruebas → implementación; ejecutar el bloque completo antes de subir, porque el commit de pruebas espera los textos de los siguientes.

```powershell
cd "C:\Users\aaroo\Documents\DesignSoftware-projectU\Yapa-publicacion"
git switch pulir-detalles

git add docs/propuestas/pulir-detalles.md
git commit -m "docs: definir avisos de armado y entregas pendientes"

git add api/tests/test_pulir_detalles.py
git commit -m "test: cubrir avisos y cierre semanal sin cambiar reglas"

git add api/src/yapa_sdd/fulfillment.py
git commit -m "fix: aclarar entregas pendientes y bloqueo de armado"

git add api/src/yapa_sdd/purchase.py
git commit -m "fix: explicar el bloqueo al registrar productos danados"

git add src/components/AdminPanel.tsx src/components/operations.test.ts src/components/operacionCelular.test.ts
git commit -m "ui: explicar horario de armado y registro de entregas"

git add docs/propuestas/pulir-detalles-validacion.md
git commit -m "docs: registrar validacion local de los avisos"

git --no-pager log -6 --oneline
git status
git push -u origin pulir-detalles
```

Detenerse si un comando da error. Una sola subida publica los seis commits nuevos, además del historial previo de la rama. Para proponer la incorporación a main: abrir un pull request con base `main` y compare `pulir-detalles`; revisarlo con el equipo antes de fusionar.

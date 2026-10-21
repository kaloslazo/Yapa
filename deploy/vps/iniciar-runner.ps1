# Inicia el runner de GitHub si no está corriendo (iteración 52, S-275). Úsalo si la VPS se reinicia.
$ErrorActionPreference = 'Stop'
$dir = 'C:\yapa\runner'
$corre = Get-WmiObject Win32_Process -Filter "Name='Runner.Listener.exe'" | Where-Object { $_.ExecutablePath -like "$dir\*" }
if ($corre) { 'El runner ya está corriendo'; return }
$r = ([wmiclass]'Win32_Process').Create("cmd.exe /c $dir\run.cmd >> $dir\runner.log 2>&1", $dir, $null)  # fuera de esta sesión
if ($r.ReturnValue -ne 0) { throw "No se pudo lanzar el runner (código $($r.ReturnValue))" }
Start-Sleep -Seconds 8
Get-Content "$dir\runner.log" -Tail 5 -ErrorAction SilentlyContinue

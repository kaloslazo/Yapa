# Despliegue automático de Yapa en la VPS (iteración 52, api/docs/desarrollo/52-despliegue-automatico.md).
# Copia de referencia: la que corre vive en la VPS (C:\yapa\ci\desplegar-ci.ps1, S-273); el flujo de GitHub solo la llama.
# Funciona en PowerShell 4 (Windows Server 2012 R2): sin Expand-Archive ni Invoke-WebRequest con redirecciones.
param(
    [string]$Repo = '',       # kaloslazo/Yapa
    [string]$RunId = '',      # ejecución del flujo de GitHub que armó el paquete
    [string]$ZipLocal = ''    # prueba: usa este paquete en vez de bajarlo de GitHub
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = 'Tls12'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$raiz = 'C:\yapa'
$ci = "$raiz\ci"
$app = "$raiz\app"
$anterior = "$raiz\app.prev"
$puerto = 8140
New-Item -ItemType Directory -Force $ci | Out-Null

function Log($texto) {
    ('{0} {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $texto) | Add-Content "$ci\despliegues.log"
    Write-Host $texto
}

# solo el motor de Yapa; los python de Neolaser y Axion no se tocan
function Parar-Motor {
    Get-WmiObject Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -like '*yapa_sdd.web*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Start-Sleep -Seconds 2
}

function Arrancar-Motor {
    $r = ([wmiclass]'Win32_Process').Create("cmd.exe /c $raiz\iniciar.cmd", $raiz, $null)  # fuera del árbol del runner: sobrevive al trabajo
    if ($r.ReturnValue -ne 0) { throw "No se pudo lanzar el motor (código $($r.ReturnValue))" }
}

function Esta-Sano {  # DA-05: hasta 40 segundos de reloj (S-274), no 40 de intentos
    $limite = (Get-Date).AddSeconds(40)
    while ((Get-Date) -lt $limite) {
        Start-Sleep -Seconds 2
        try {
            $respuesta = Invoke-WebRequest "http://127.0.0.1:$puerto/salud" -UseBasicParsing -TimeoutSec 3
            if ($respuesta.Content -match '"ok":\s*true') { return $true }
        } catch { }
    }
    return $false
}

# DA-06: el paquete se revisa antes de tocar la versión que corre
function Validar-Paquete($zip) {
    if (-not (Test-Path $zip) -or (Get-Item $zip).Length -lt 100KB) { throw 'El paquete falta o es demasiado chico' }
    $abierto = [IO.Compression.ZipFile]::OpenRead($zip)
    try { $nombres = @($abierto.Entries | ForEach-Object { $_.FullName.Replace('\', '/') }) } finally { $abierto.Dispose() }
    foreach ($necesario in 'dist/index.html', 'api/src/yapa_sdd/web/__main__.py') {
        if ($nombres -notcontains $necesario) { throw "Al paquete le falta $necesario" }
    }
}

# S-272: token temporal del trabajo de GitHub. La dirección de bajada responde 302 hacia un almacén firmado:
# se sigue a mano para no mandar el token a ese almacén.
function Bajar-Artefacto($repo, $runId, $destino) {
    $token = $env:GITHUB_TOKEN
    if (-not $token) { throw 'Falta GITHUB_TOKEN (lo da el trabajo de GitHub)' }
    if ($repo -notmatch '^[\w.-]+/[\w.-]+$' -or $runId -notmatch '^\d+$') { throw 'Repositorio o ejecución con formato raro' }
    $cabeceras = @{ Authorization = "Bearer $token"; 'User-Agent' = 'yapa-despliegue'; Accept = 'application/vnd.github+json' }
    $lista = Invoke-RestMethod "https://api.github.com/repos/$repo/actions/runs/$runId/artifacts" -Headers $cabeceras
    $artefacto = $lista.artifacts | Where-Object { $_.name -eq 'yapa-app' -and -not $_.expired } | Select-Object -First 1
    if (-not $artefacto) { throw 'No hay un artefacto yapa-app vigente en esta ejecución' }
    $pedido = [Net.HttpWebRequest]::Create($artefacto.archive_download_url)
    $pedido.AllowAutoRedirect = $false
    $pedido.UserAgent = 'yapa-despliegue'
    $pedido.Headers.Add('Authorization', "Bearer $token")
    try { $respuesta = $pedido.GetResponse() } catch [Net.WebException] { $respuesta = $_.Exception.Response }
    $firmada = $respuesta.Headers['Location']
    $codigo = [int]$respuesta.StatusCode
    $respuesta.Close()
    if ($codigo -ne 302 -or -not $firmada) { throw "La bajada no redirigió al almacén (código $codigo)" }
    (New-Object Net.WebClient).DownloadFile($firmada, $destino)
}

function Restaurar($motivo) {  # DA-05
    Log "restaurando la versión anterior: $motivo"
    Parar-Motor
    if (Test-Path $app) { Remove-Item $app -Recurse -Force }
    Move-Item $anterior $app
    Arrancar-Motor
    if (Esta-Sano) { Log 'restaurado · la versión anterior vuelve a responder' } else { Log 'ERROR GRAVE: tampoco responde la versión anterior' }
}

$cambiado = $false
try {
    Log "inicio · ejecución '$RunId'"
    $zip = "$ci\yapa-app.zip"
    if ($ZipLocal) { Copy-Item $ZipLocal $zip -Force } else { Bajar-Artefacto $Repo $RunId $zip }
    Validar-Paquete $zip

    try { & "$raiz\respaldar.ps1" | Out-Null; Log 'base respaldada' } catch { Log "aviso: no se pudo respaldar ($_)" }  # S-274

    Parar-Motor
    if (Test-Path $anterior) { Remove-Item $anterior -Recurse -Force }
    if (Test-Path $app) { Move-Item $app $anterior }
    $cambiado = $true
    [IO.Compression.ZipFile]::ExtractToDirectory($zip, $app)
    Arrancar-Motor

    if (-not (Esta-Sano)) { throw 'la versión nueva no respondió /salud en 40 segundos' }
    Log 'ok · versión nueva activa'
    try { Log ('público: ' + (Invoke-WebRequest 'https://holayapa.app/salud' -UseBasicParsing -TimeoutSec 15).Content) } catch { Log "aviso: no se pudo comprobar holayapa.app ($_)" }
} catch {
    $motivo = $_.Exception.Message
    Log "FALLÓ: $motivo"
    if ($cambiado -and (Test-Path $anterior)) { Restaurar $motivo }
    exit 1
}

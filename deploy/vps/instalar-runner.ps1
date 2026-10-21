# Registra e inicia el runner de GitHub en la VPS (iteración 52, S-275). Se corre UNA vez.
# El código de registro lo genera quien administra el repo (Settings > Actions > Runners > New self-hosted runner)
# y vale una hora. Corre como programa normal, sin servicio de Windows: no arranca solo.
param(
    [Parameter(Mandatory = $true)][string]$Token,
    [string]$Url = 'https://github.com/kaloslazo/Yapa',
    [string]$Version = '2.338.0'
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = 'Tls12'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$dir = 'C:\yapa\runner'
if (-not (Test-Path "$dir\config.cmd")) {
    $zip = 'C:\yapa\runner.zip'
    (New-Object Net.WebClient).DownloadFile("https://github.com/actions/runner/releases/download/v$Version/actions-runner-win-x64-$Version.zip", $zip)
    [IO.Compression.ZipFile]::ExtractToDirectory($zip, $dir)
    Remove-Item $zip -Force
}
Set-Location $dir
& cmd.exe /c "config.cmd --unattended --url $Url --token $Token --name vps-yapa --labels yapa-vps --work _work --replace"
if ($LASTEXITCODE -ne 0) { throw "config.cmd falló ($LASTEXITCODE)" }
& "$PSScriptRoot\iniciar-runner.ps1"

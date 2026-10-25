# Avvia Open Score sulla LAN scolastica.
#
# Esempio:
#   powershell -ExecutionPolicy Bypass -File start-open-score.ps1
#   powershell -ExecutionPolicy Bypass -File start-open-score.ps1 -Port 8080
#
# Richiede che torneo-lab\.venv esista e che open-score.env sia configurato.

param(
    [string]$EnvFile = (Join-Path $PSScriptRoot 'open-score.env'),
    [string]$HostAddress = '0.0.0.0',
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
$LabDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'torneo-lab'
$Python = Join-Path $LabDir '.venv\Scripts\python.exe'

if (-not (Test-Path $Python)) {
    throw "Interprete non trovato: $Python. Creare prima l'ambiente con py -m venv .venv e installare requirements.txt."
}

if (Test-Path $EnvFile) {
    foreach ($line in Get-Content $EnvFile) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $separator = $trimmed.IndexOf('=')
        if ($separator -lt 1) { continue }
        $name = $trimmed.Substring(0, $separator).Trim()
        $value = $trimmed.Substring($separator + 1).Trim()
        Set-Item -Path "Env:$name" -Value $value
    }
    Write-Host "Configurazione caricata da $EnvFile"
} else {
    Write-Warning "File di configurazione assente: $EnvFile. Il server partira in sola lettura finche non viene creato un account docente."
}

if (-not $env:TORNEO_ALLOWED_HOSTS -and $HostAddress -ne '127.0.0.1') {
    Write-Warning "TORNEO_ALLOWED_HOSTS non impostato: solo 127.0.0.1, localhost e testserver saranno accettati."
}

Write-Host "Open Score in ascolto su http://${HostAddress}:$Port (un solo worker, SQLite)"
Write-Host "Premere Ctrl+C per fermare il server."

Push-Location $LabDir
try {
    & $Python -m uvicorn app:app --host $HostAddress --port $Port --workers 1 --proxy-headers
    exit $LASTEXITCODE
} finally {
    Pop-Location
}

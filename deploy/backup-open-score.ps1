# Backup consistente del database Open Score.
#
# Usa "VACUUM INTO" tramite backup.py: il file prodotto e leggibile anche
# mentre il server sta scrivendo. Conserva gli ultimi 14 backup per default.
#
# Esempio manuale:
#   powershell -ExecutionPolicy Bypass -File backup-open-score.ps1
#   powershell -ExecutionPolicy Bypass -File backup-open-score.ps1 -Keep 30

param(
    [string]$EnvFile = (Join-Path $PSScriptRoot 'open-score.env'),
    [int]$Keep = 14
)

$ErrorActionPreference = 'Stop'
$LabDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'torneo-lab'
$Python = Join-Path $LabDir '.venv\Scripts\python.exe'
$BackupDir = Join-Path $LabDir 'backup'
$LogFile = Join-Path $BackupDir 'backup.log'

if (Test-Path $EnvFile) {
    foreach ($line in Get-Content $EnvFile) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $separator = $trimmed.IndexOf('=')
        if ($separator -lt 1) { continue }
        Set-Item -Path "Env:$($trimmed.Substring(0, $separator).Trim())" `
                 -Value $trimmed.Substring($separator + 1).Trim()
    }
}

$Database = if ($env:TORNEO_DB_PATH) { $env:TORNEO_DB_PATH } `
            else { Join-Path $LabDir 'data\open_score.sqlite3' }
New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null

$stamp = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
try {
    $created = & $Python (Join-Path $LabDir 'backup.py') --db $Database `
                --out $BackupDir --keep $Keep
    if ($LASTEXITCODE -ne 0) { throw "backup.py ha restituito $LASTEXITCODE" }
    Add-Content -Path $LogFile -Value "$stamp OK $created" -Encoding utf8
    Write-Host "Backup creato: $created"
} catch {
    Add-Content -Path $LogFile -Value "$stamp ERRORE $($_.Exception.Message)" -Encoding utf8
    throw
}

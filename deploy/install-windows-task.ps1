# Registra Open Score come attivita pianificata di Windows.
#
#   powershell -ExecutionPolicy Bypass -File install-windows-task.ps1
#   powershell -ExecutionPolicy Bypass -File install-windows-task.ps1 -BackupTime 19:00
#   powershell -ExecutionPolicy Bypass -File install-windows-task.ps1 -Remove
#
# Va eseguito come amministratore: l'attivita parte all'avvio del computer
# con l'account SYSTEM, quindi il server e disponibile anche senza login.
# Non usare questo metodo insieme al servizio systemd o a NSSM.

param(
    [string]$TaskName = 'Open Score',
    [string]$BackupTaskName = 'Open Score backup',
    [string]$BackupTime = '18:30',
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]$identity
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    throw 'Eseguire PowerShell come amministratore per registrare le attivita di sistema.'
}

if ($Remove) {
    foreach ($name in @($TaskName, $BackupTaskName)) {
        if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
            Unregister-ScheduledTask -TaskName $name -Confirm:$false
            Write-Host "Attivita rimossa: $name"
        }
    }
    return
}

$StartScript = Join-Path $PSScriptRoot 'start-open-score.ps1'
$BackupScript = Join-Path $PSScriptRoot 'backup-open-score.ps1'
$LabDir = Join-Path (Split-Path -Parent $PSScriptRoot) 'torneo-lab'
$PowerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'

foreach ($script in @($StartScript, $BackupScript)) {
    if (-not (Test-Path $script)) { throw "Script non trovato: $script" }
}

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)
$system = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount `
    -RunLevel Highest

$serverAction = New-ScheduledTaskAction -Execute $PowerShell `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`"" `
    -WorkingDirectory $LabDir
$serverTrigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName $TaskName -Action $serverAction `
    -Trigger $serverTrigger -Settings $settings -Principal $system `
    -Description 'Server web Open Score per la LAN scolastica' -Force | Out-Null
Write-Host "Attivita registrata all'avvio: $TaskName"

$backupAction = New-ScheduledTaskAction -Execute $PowerShell `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$BackupScript`"" `
    -WorkingDirectory $LabDir
$backupTrigger = New-ScheduledTaskTrigger -Daily -At $BackupTime
Register-ScheduledTask -TaskName $BackupTaskName -Action $backupAction `
    -Trigger $backupTrigger -Settings $settings -Principal $system `
    -Description 'Backup giornaliero del database Open Score' -Force | Out-Null
Write-Host "Attivita backup registrata ogni giorno alle $BackupTime`: $BackupTaskName"

Write-Host ''
Write-Host 'Comandi utili:'
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo"
Write-Host "  Stop-ScheduledTask -TaskName '$TaskName'"

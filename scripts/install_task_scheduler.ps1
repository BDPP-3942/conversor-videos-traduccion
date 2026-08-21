param(
    [string]$TaskName = "VideoTranslationPipeline",
    [string]$Executable = ""
)

$ErrorActionPreference = "Stop"
$AppRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($Executable)) {
    $Executable = Join-Path $AppRoot "VideoTranslationPipeline.exe"
}
if (-not (Test-Path $Executable)) {
    throw "No se encuentra el ejecutable: $Executable"
}

$WorkDir = Split-Path -Parent $Executable
$Action = New-ScheduledTaskAction `
    -Execute $Executable `
    -Argument "run --scheduled" `
    -WorkingDirectory $WorkDir

$Trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddMinutes(1)) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Password `
    -RunLevel Limited

$Settings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 24)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force | Out-Null
Write-Host "Tarea creada: $TaskName"
Write-Host "Ejecutable: $Executable"
Write-Host "Directorio de trabajo: $WorkDir"
Write-Host "La primera configuración OAuth debe hacerse antes de activar la ejecución desatendida."

@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$roots = @('HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'); ^
   $app = Get-ItemProperty -Path $roots -ErrorAction SilentlyContinue | Where-Object { $_.DisplayName -eq 'Video Translation Pipeline' } | Select-Object -First 1; ^
   if (-not $app) { Write-Error 'No se ha encontrado una instalación de Video Translation Pipeline.'; exit 1 }; ^
   $productCode = $app.PSChildName; ^
   Start-Process -FilePath 'msiexec.exe' -ArgumentList @('/x', $productCode) -Wait"
if errorlevel 1 (
  echo No se ha podido iniciar la desinstalacion.
  exit /b 1
)
exit /b 0

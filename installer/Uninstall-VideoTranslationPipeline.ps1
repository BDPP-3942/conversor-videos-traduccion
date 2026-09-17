$ErrorActionPreference = "Stop"

# Desinstala únicamente la aplicación MSI. Los datos de usuario están fuera
# de INSTALLFOLDER y no se eliminan mediante este proceso.
$roots = @(
  "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
  "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
$app = Get-ItemProperty $roots -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName -eq "Video Translation Pipeline" } |
  Select-Object -First 1

if (-not $app -or -not $app.PSChildName) {
  throw "No se ha encontrado una instalación MSI de Video Translation Pipeline."
}

$code = $app.PSChildName
Start-Process -FilePath "msiexec.exe" -ArgumentList "/x $code" -Wait -Verb RunAs

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonPath = Join-Path $ProjectDir ".venv\Scripts\python.exe"

$processes = Get-CimInstance Win32_Process |
  Where-Object {
    $_.ExecutablePath -eq $PythonPath -and
    $_.CommandLine -like "*main.py*"
  }

if (-not $processes) {
  Write-Host "Translator is not running."
  exit 0
}

foreach ($process in $processes) {
  Stop-Process -Id $process.ProcessId -Force
  Write-Host "Stopped translator process $($process.ProcessId)."
}

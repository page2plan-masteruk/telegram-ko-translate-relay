$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$LogDir = Join-Path $ProjectDir "logs"
$OutLog = Join-Path $LogDir "translator.out.log"
$ErrLog = Join-Path $LogDir "translator.err.log"

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

$running = Get-CimInstance Win32_Process |
  Where-Object {
    $_.ExecutablePath -eq $Python -and
    $_.CommandLine -like "*main.py*"
  }

if ($running) {
  Write-Host "Translator is already running."
  $running | ForEach-Object { Write-Host "Process ID: $($_.ProcessId)" }
  exit 0
}

Start-Process `
  -FilePath $Python `
  -ArgumentList "-u", "main.py" `
  -WorkingDirectory $ProjectDir `
  -RedirectStandardOutput $OutLog `
  -RedirectStandardError $ErrLog `
  -WindowStyle Hidden

Write-Host "Translator started."
Write-Host "Output log: $OutLog"
Write-Host "Error log:  $ErrLog"

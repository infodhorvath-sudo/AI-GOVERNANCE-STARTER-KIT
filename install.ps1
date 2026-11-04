# Thin wrapper for Windows PowerShell. Same flags as install.py:  .\install.ps1 --dry-run
Set-Location $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) { & py -3 install.py @args }
elseif (Get-Command python -ErrorAction SilentlyContinue) { & python install.py @args }
else { Write-Host "Python 3.8+ is required: https://www.python.org/downloads/"; exit 1 }

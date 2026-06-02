# Startet Outlook-Ingest mit der Projekt-venv (kein Activate noetig).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Keine .venv gefunden. Einmalig: py -3.11 -m venv .venv; pip install -e `".[dev]`""
}
& $python (Join-Path $root "scripts\run_outlook_ingest.py") @args
exit $LASTEXITCODE

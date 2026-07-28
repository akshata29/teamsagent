# Start the demo backend (creates/activates .venv, installs deps, runs uvicorn).
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"

python -m pip install --upgrade pip
pip install -r requirements.txt

$env:PYTHONPATH = "$PSScriptRoot;$(Split-Path $PSScriptRoot -Parent)"
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload

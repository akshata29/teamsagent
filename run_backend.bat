@echo off
REM Start the demo backend (FastAPI + Uvicorn) in offline-capable mode.
cd /d "%~dp0backend"
if not exist ".venv" (
    python -m venv .venv
    python -m pip install --upgrade pip
    pip install -r requirements.txt
)
call ".venv\Scripts\activate.bat"
set PYTHONPATH=%~dp0backend;%~dp0
uvicorn app.main:app --host 0.0.0.0 --port 8010 --reload

@echo off
REM Launch backend and frontend in separate windows.
start "CapMarkets Backend" cmd /k "%~dp0run_backend.bat"
start "CapMarkets Frontend" cmd /k "%~dp0run_frontend.bat"
echo Backend: http://localhost:8010/api/health
echo Frontend: http://localhost:5173

@echo off
REM Launch backend, Option B proxy, and Agents Playground in separate windows.
REM (Option B = per-user OBO. Playground has no SSO, so results are public-only there;
REM use local Teams sideload for the real per-user OBO test.)
start "CapMarkets Backend" cmd /k "%~dp0run_backend.bat"
start "CapMarkets Option B Proxy" cmd /k "%~dp0run_proxy.bat"
timeout /t 6 >nul
start "Agents Playground" cmd /k "%~dp0run_playground.bat"
echo Backend:    http://localhost:8010/api/health
echo Proxy bot:  http://localhost:3978/api/messages
echo Playground: http://localhost:56150

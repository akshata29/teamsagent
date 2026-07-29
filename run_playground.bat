@echo off
REM Launch Microsoft 365 Agents Playground pointed at the local proxy bot (:3978).
REM Start run_proxy.bat first. Opens the Playground UI at http://localhost:56150.
where agentsplayground >nul 2>nul || npm install -g @microsoft/m365agentsplayground
agentsplayground -e http://localhost:3978/api/messages -c msteams

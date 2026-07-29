@echo off
REM Start the Option B Custom Engine Agent proxy (Agents SDK bot on :3978, Playground config).
REM Requires the backend running on :8010 (run_backend.bat).
cd /d "%~dp0proxy"
if not exist "node_modules" (
    npm install
)
npm run dev:teamsfx:playground

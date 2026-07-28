@echo off
REM Start the demo frontend (Vite dev server on :5173, proxies /api to :8010).
cd /d "%~dp0frontend"
if not exist "node_modules" (
    npm install
)
npm run dev

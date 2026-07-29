@echo off
REM Start the Option B Custom Engine Agent proxy for TEAMS (Agents SDK bot on :3978).
REM Loads proxy\.localConfigs (finagents bot creds + REQUIRE_SSO=true + DEBUG=agents:*).
REM Requires: backend on :8010 (run_backend.bat) AND the devtunnel forwarding :3978.
cd /d "%~dp0proxy"
if not exist "node_modules" (
    npm install
)
npm run dev:teamsfx

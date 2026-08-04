@echo off
REM Host the persistent 'capmarkets-obo' dev tunnel that forwards :3978.
REM Keeps the fixed URL https://p6mx573x-3978.use.devtunnels.ms so Azure Bot Service,
REM the search-sso OAuth connection, and the finagents app registration stay valid
REM (no Azure updates needed). Run this BEFORE run_proxy_teams.bat.
devtunnel host capmarkets-obo

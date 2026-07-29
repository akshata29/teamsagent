<#
.SYNOPSIS
  Finalize local Teams sideload assets WITHOUT the M365 Agents Toolkit CLI:
    - Write proxy/.localConfigs (runtime bot creds the Agents SDK reads).
    - Populate BOT_ID / TEAMS_APP_ID in proxy/env/.env.local.
    - Render appPackage/manifest.json placeholders and zip a sideloadable package.

  Uses the finagents app as the single bot + SSO/OBO identity. Run AFTER
  setup_local_bot.ps1 has created the Azure Bot + search-sso OAuth connection.
#>
param(
    [string] $ClientId = "fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c",
    [string] $TenantId = "37f28838-9a79-4b20-a28a-c7d8a85e4eda",
    [string] $BotDomain = "p6mx573x-3978.use.devtunnels.ms",
    [string] $ConnectionName = "search-sso",
    [string] $OboScope = "https://search.azure.com/.default",
    [string] $BackendUrl = "http://localhost:8010",
    [string] $PersonaId = "equity-research"
)

$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$proxy = Join-Path $root "proxy"

# 1. finagents secret (never printed).
$secret = $null
$envPath = Join-Path $root "backend\.env"
if (Test-Path $envPath) {
    $line = Get-Content $envPath | Where-Object { $_ -match '^AAD_CLIENT_SECRET=' } | Select-Object -First 1
    if ($line) { $secret = ($line -split '=', 2)[1].Trim() }
}
if (-not $secret) { throw "AAD_CLIENT_SECRET not found in backend/.env" }

# 2. Reuse an existing TEAMS_APP_ID from .env.local, else generate one.
$envLocalPath = Join-Path $proxy "env\.env.local"
$envLocal = Get-Content $envLocalPath
$teamsAppLine = $envLocal | Where-Object { $_ -match '^TEAMS_APP_ID=' } | Select-Object -First 1
$teamsAppId = ($teamsAppLine -split '=', 2)[1].Trim()
if (-not $teamsAppId) { $teamsAppId = [guid]::NewGuid().ToString() }

# 3. Update BOT_ID + TEAMS_APP_ID in .env.local.
$envLocal = $envLocal | ForEach-Object {
    if ($_ -match '^BOT_ID=')      { "BOT_ID=$ClientId" }
    elseif ($_ -match '^TEAMS_APP_ID=') { "TEAMS_APP_ID=$teamsAppId" }
    else { $_ }
}
Set-Content -Path $envLocalPath -Value $envLocal -Encoding UTF8
Write-Host "Updated .env.local (BOT_ID + TEAMS_APP_ID=$teamsAppId)" -ForegroundColor Green

# 4. Write proxy/.localConfigs (runtime env the Agents SDK reads via env-cmd).
$localConfigs = @(
    "clientId=$ClientId",
    "clientSecret=$secret",
    "tenantId=$TenantId",
    "BACKEND_URL=$BackendUrl",
    "AAD_OAUTH_CONNECTION_NAME=$ConnectionName",
    "OBO_SCOPE=$OboScope",
    "DEMO_PERSONA_ID=$PersonaId",
    "REQUIRE_SSO=true",
    "PORT=3978"
)
Set-Content -Path (Join-Path $proxy ".localConfigs") -Value $localConfigs -Encoding UTF8
Write-Host "Wrote proxy/.localConfigs" -ForegroundColor Green

# 5. Render manifest placeholders and zip the app package.
$buildDir = Join-Path $proxy "appPackage\build"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
$manifest = Get-Content (Join-Path $proxy "appPackage\manifest.json") -Raw
$manifest = $manifest.Replace('${{TEAMS_APP_ID}}', $teamsAppId)
$manifest = $manifest.Replace('${{BOT_ID}}', $ClientId)
$manifest = $manifest.Replace('${{AAD_APP_CLIENT_ID}}', $ClientId)
# webApplicationInfo.resource must be the plain api://<client-id> form (matches the
# OAuth Token Exchange URL) or Teams SSO fails with resourcematchfailed.
$manifest = $manifest.Replace('api://${{BOT_DOMAIN}}/' + $ClientId, 'api://' + $ClientId)
$manifest = $manifest.Replace('${{BOT_DOMAIN}}', $BotDomain)
# Ensure token.botframework.com + bot domain are valid domains for SSO.
$manifest = $manifest.Replace('"validDomains": [],', '"validDomains": ["token.botframework.com", "' + $BotDomain + '"],')
$renderedManifest = Join-Path $buildDir "manifest.json"
Set-Content -Path $renderedManifest -Value $manifest -Encoding UTF8

Copy-Item (Join-Path $proxy "appPackage\color.png") $buildDir -Force
Copy-Item (Join-Path $proxy "appPackage\outline.png") $buildDir -Force

$zipPath = Join-Path $buildDir "appPackage.local.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $buildDir "manifest.json"), (Join-Path $buildDir "color.png"), (Join-Path $buildDir "outline.png") -DestinationPath $zipPath -Force
Write-Host "Built $zipPath" -ForegroundColor Green

Write-Host ""
Write-Host "Local Teams assets ready." -ForegroundColor Cyan
Write-Host "  TEAMS_APP_ID : $teamsAppId"
Write-Host "  BOT_ID       : $ClientId"
Write-Host "  Sideload zip : $zipPath"

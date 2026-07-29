<#
.SYNOPSIS
  Provision a BRAND-NEW bot identity (new app registration => new botId => new Teams
  conversation) with canonical Teams SSO config, so SSO works on a fresh chat that is
  not bound to the old poisoned conversation. Wires the Azure Bot + OAuth connection,
  writes proxy/.localConfigs, renders the manifest, and zips a sideloadable package.

  All three SSO values are identical api://<new-appId>:
    - app identifierUri
    - manifest webApplicationInfo.resource
    - OAuth connection tokenExchangeUrl
  The SSO connection is scoped to the app's OWN access_as_user (not a foreign resource).
#>
param(
    [string] $BotName      = "capmarkets-obo-bot2",
    [string] $ResourceGroup = "astdataai",
    [string] $TenantId     = "37f28838-9a79-4b20-a28a-c7d8a85e4eda",
    [string] $BotDomain    = "p6mx573x-3978.use.devtunnels.ms",
    [string] $ConnectionName = "search-sso",
    [string] $OboScope     = "https://search.azure.com/.default",
    [string] $BackendUrl   = "http://localhost:8010",
    [string] $PersonaId    = "equity-research"
)

$ErrorActionPreference = "Stop"
$root  = Split-Path $PSScriptRoot -Parent
$proxy = Join-Path $root "proxy"

# Azure Cognitive Search delegated app + user_impersonation scope (for OBO).
$SearchAppId   = "880da380-985e-4198-81b9-e05b1cc53158"
$SearchScopeId = "a4165a31-5d9e-4120-bd1e-9d88c66fd3b8"
# Teams / M365 first-party client app IDs to pre-authorize on access_as_user.
$TeamsClients = @(
    "1fec8e78-bce4-4aaf-ab1b-5451cc387264",
    "5e3ce6c0-2b1f-4285-8d4b-75ee78787346",
    "4765445b-32c6-49b0-83e6-1d93765276ca",
    "0ec893e0-5785-4de6-99da-4ed124e5296c",
    "d3590ed6-52b3-4102-aeff-aad2292ab01c",
    "27922004-5251-4030-b22d-91ecd9a37ea4"
)

Write-Host "1/8 Creating app registration '$BotName'..." -ForegroundColor Cyan
$app   = az ad app create --display-name $BotName --sign-in-audience AzureADMyOrg -o json | ConvertFrom-Json
$appId = $app.appId
$objId = $app.id
Write-Host "    appId=$appId" -ForegroundColor DarkGray

Write-Host "2/8 Configuring identifierUri + access_as_user + redirect + Teams pre-auth..." -ForegroundColor Cyan
$scopeId = [guid]::NewGuid().ToString()
$preAuth = @()
foreach ($c in $TeamsClients) { $preAuth += @{ appId = $c; delegatedPermissionIds = @($scopeId) } }
$patch = @{
    identifierUris = @("api://$appId")
    api = @{
        oauth2PermissionScopes = @(@{
            id = $scopeId
            adminConsentDescription = "Access CapMarkets Research as the signed-in user"
            adminConsentDisplayName = "Access as user"
            userConsentDescription  = "Access CapMarkets Research as you"
            userConsentDisplayName   = "Access as user"
            value = "access_as_user"
            type  = "User"
            isEnabled = $true
        })
        preAuthorizedApplications = $preAuth
    }
    web = @{ redirectUris = @("https://token.botframework.com/.auth/web/redirect") }
}
$patchPath = Join-Path $env:TEMP "freshbot_patch.json"
($patch | ConvertTo-Json -Depth 12) | Out-File -FilePath $patchPath -Encoding utf8
az rest --method patch --url "https://graph.microsoft.com/v1.0/applications/$objId" --headers "Content-Type=application/json" --body "@$patchPath" -o none

Write-Host "3/8 Creating client secret..." -ForegroundColor Cyan
$secret = az ad app credential reset --id $appId --display-name "proxy" --years 1 --query password -o tsv

Write-Host "4/8 Creating service principal..." -ForegroundColor Cyan
az ad sp create --id $appId -o none 2>$null

Write-Host "5/8 Adding delegated Azure Search permission + admin consent..." -ForegroundColor Cyan
az ad app permission add --id $appId --api $SearchAppId --api-permissions "$SearchScopeId=Scope" -o none 2>$null
Start-Sleep -Seconds 5
try { az ad app permission admin-consent --id $appId -o none 2>$null; Write-Host "    admin consent granted" -ForegroundColor DarkGray }
catch { Write-Host "    admin consent deferred (SSO still works; OBO can be consented later)" -ForegroundColor Yellow }

Write-Host "6/8 Creating Azure Bot + Teams channel + OAuth connection..." -ForegroundColor Cyan
az bot create --resource-group $ResourceGroup --name $BotName --app-type SingleTenant --appid $appId --tenant-id $TenantId --endpoint "https://$BotDomain/api/messages" --sku F0 --only-show-errors -o none
az bot msteams create --resource-group $ResourceGroup --name $BotName --only-show-errors -o none
az bot authsetting create `
    --resource-group $ResourceGroup --name $BotName --setting-name $ConnectionName `
    --client-id $appId --client-secret $secret --service Aadv2 `
    --provider-scope-string "api://$appId/access_as_user" `
    --parameters "clientId=$appId" "clientSecret=$secret" "tenantId=$TenantId" "tokenExchangeUrl=api://$appId" `
    --only-show-errors -o none

Write-Host "7/8 Writing proxy config (.localConfigs + .env.local)..." -ForegroundColor Cyan
$localConfigs = @(
    "clientId=$appId",
    "clientSecret=$secret",
    "tenantId=$TenantId",
    "BACKEND_URL=$BackendUrl",
    "AAD_OAUTH_CONNECTION_NAME=$ConnectionName",
    "OBO_SCOPE=$OboScope",
    "DEMO_PERSONA_ID=$PersonaId",
    "REQUIRE_SSO=true",
    "PORT=3978",
    "DEBUG=agents:*"
)
Set-Content -Path (Join-Path $proxy ".localConfigs") -Value $localConfigs -Encoding UTF8

$teamsAppId  = [guid]::NewGuid().ToString()
$envLocalPath = Join-Path $proxy "env\.env.local"
$envLocal = Get-Content $envLocalPath | ForEach-Object {
    if ($_ -match '^BOT_ID=')           { "BOT_ID=$appId" }
    elseif ($_ -match '^TEAMS_APP_ID=') { "TEAMS_APP_ID=$teamsAppId" }
    else { $_ }
}
Set-Content -Path $envLocalPath -Value $envLocal -Encoding UTF8

Write-Host "8/8 Rendering manifest + zipping package..." -ForegroundColor Cyan
$buildDir = Join-Path $proxy "appPackage\build"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
$manifest = Get-Content (Join-Path $proxy "appPackage\manifest.json") -Raw
$manifest = $manifest.Replace('${{TEAMS_APP_ID}}', $teamsAppId)
$manifest = $manifest.Replace('${{BOT_ID}}', $appId)
$manifest = $manifest.Replace('${{AAD_APP_CLIENT_ID}}', $appId)
$manifest = $manifest.Replace('api://${{BOT_DOMAIN}}/' + $appId, 'api://' + $appId)
$manifest = $manifest.Replace('${{BOT_DOMAIN}}', $BotDomain)
$manifest = $manifest.Replace('"validDomains": [],', '"validDomains": ["token.botframework.com", "' + $BotDomain + '"],')
Set-Content -Path (Join-Path $buildDir "manifest.json") -Value $manifest -Encoding UTF8
Copy-Item (Join-Path $proxy "appPackage\color.png") $buildDir -Force
Copy-Item (Join-Path $proxy "appPackage\outline.png") $buildDir -Force
$zipPath = Join-Path $buildDir "appPackage.local.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $buildDir "manifest.json"), (Join-Path $buildDir "color.png"), (Join-Path $buildDir "outline.png") -DestinationPath $zipPath -Force

Write-Host ""
Write-Host "DONE. Fresh bot provisioned." -ForegroundColor Green
Write-Host "  New appId/botId : $appId" -ForegroundColor Green
Write-Host "  TEAMS_APP_ID    : $teamsAppId" -ForegroundColor Green
Write-Host "  Resource/URI    : api://$appId (identifierUri = manifest resource = tokenExchangeUrl)" -ForegroundColor Green
Write-Host "  Sideload zip    : $zipPath" -ForegroundColor Green

<#
.SYNOPSIS
  Provision a real Azure Bot resource for the Option B Teams proxy (local/devtunnel),
  backed by the existing `finagents` app registration, and wire the Teams SSO + OBO
  OAuth connection. Uses the working `az` session (browser/device login) instead of the
  M365 Agents Toolkit CLI, whose Windows WAM broker login is broken in this environment.

.DESCRIPTION
  Steps:
    1. Read the finagents client secret from backend/.env (AAD_CLIENT_SECRET).
    2. Create the Azure Bot resource (SingleTenant, appid = finagents) with the devtunnel
       messaging endpoint.
    3. Add the Microsoft Teams channel.
    4. Create the `search-sso` OAuth connection (AAD v2, finagents client id/secret) with a
       token-exchange URL that matches the Teams manifest webApplicationInfo.resource.

  The finagents Application ID URI + Teams client pre-authorization are handled separately
  (see setup_finagents_sso.ps1 / az rest calls) because they modify the app registration.

.EXAMPLE
  ./deploy/setup_local_bot.ps1
#>
param(
    [string] $BotName = "capmarkets-obo-bot",
    [string] $ResourceGroup = "astdataai",
    [string] $FinAgentsClientId = "fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c",
    [string] $TenantId = "37f28838-9a79-4b20-a28a-c7d8a85e4eda",
    [string] $BotDomain = "p6mx573x-3978.use.devtunnels.ms",
    [string] $ConnectionName = "search-sso",
    [string] $Scopes = "https://search.azure.com/.default"
)

$ErrorActionPreference = "Stop"

# 1. Load finagents secret from backend/.env (never printed).
$envPath = Join-Path $PSScriptRoot "..\backend\.env"
$secret = $null
if (Test-Path $envPath) {
    $line = Get-Content $envPath | Where-Object { $_ -match '^AAD_CLIENT_SECRET=' } | Select-Object -First 1
    if ($line) { $secret = ($line -split '=', 2)[1].Trim() }
}
if (-not $secret) { throw "AAD_CLIENT_SECRET not found in backend/.env" }
Write-Host ("finagents secret loaded (len={0})" -f $secret.Length) -ForegroundColor DarkGray

$endpoint = "https://$BotDomain/api/messages"
# Domain-qualified form to match the manifest resource cached by the Teams web client
# (api://<domain>/<client-id>). finagents exposes both this and the plain URI.
$tokenExchangeUrl = "api://$BotDomain/$FinAgentsClientId"

# 2. Create the Azure Bot resource (idempotent-ish: skip if it already exists).
$ErrorActionPreference = "SilentlyContinue"
$exists = az bot show --resource-group $ResourceGroup --name $BotName --query name -o tsv 2>$null
$ErrorActionPreference = "Stop"
if ($exists) {
    Write-Host "Azure Bot '$BotName' already exists - updating endpoint." -ForegroundColor Yellow
    az bot update --resource-group $ResourceGroup --name $BotName --endpoint $endpoint --only-show-errors -o none
} else {
    Write-Host "Creating Azure Bot '$BotName' (SingleTenant, appid $FinAgentsClientId)..." -ForegroundColor Cyan
    az bot create `
        --resource-group $ResourceGroup `
        --name $BotName `
        --app-type SingleTenant `
        --appid $FinAgentsClientId `
        --tenant-id $TenantId `
        --endpoint $endpoint `
        --sku F0 `
        --only-show-errors -o none
}

# 3. Add the Microsoft Teams channel.
Write-Host "Enabling Microsoft Teams channel..." -ForegroundColor Cyan
az bot msteams create --resource-group $ResourceGroup --name $BotName --only-show-errors -o none

# 4. Create the search-sso OAuth connection.
Write-Host "Creating OAuth connection '$ConnectionName' (tokenExchangeUrl=$tokenExchangeUrl)..." -ForegroundColor Cyan
az bot authsetting create `
    --resource-group $ResourceGroup `
    --name $BotName `
    --setting-name $ConnectionName `
    --client-id $FinAgentsClientId `
    --client-secret $secret `
    --service Aadv2 `
    --provider-scope-string $Scopes `
    --parameters "clientId=$FinAgentsClientId" "clientSecret=$secret" "tenantId=$TenantId" "tokenExchangeUrl=$tokenExchangeUrl" `
    --only-show-errors -o none

Write-Host ""
Write-Host "Azure Bot provisioned." -ForegroundColor Green
Write-Host "  Bot            : $BotName (rg $ResourceGroup)" -ForegroundColor Green
Write-Host "  App (bot+SSO)  : finagents $FinAgentsClientId" -ForegroundColor Green
Write-Host "  Endpoint       : $endpoint" -ForegroundColor Green
Write-Host "  OAuth conn     : $ConnectionName -> $Scopes" -ForegroundColor Green
Write-Host "  TokenExchange  : $tokenExchangeUrl" -ForegroundColor Green

<#
.SYNOPSIS
  Create the Azure Bot Service OAuth connection used by the Option B proxy for
  Teams SSO + On-Behalf-Of (OBO) to Azure AI Search.

.DESCRIPTION
  The Agents SDK proxy (proxy/src/agent.ts) references an OAuth connection by name
  (AAD_OAUTH_CONNECTION_NAME, default "search-sso"). That connection must exist on the
  Azure Bot resource created by `atk provision`, and it must be configured with the
  *finagents* app registration — which already holds the delegated Azure AI Search
  permission + admin consent needed for the OBO exchange.

  Flow:  Teams SSO token (audience = finagents)
           -> Bot OAuth connection (AAD v2, finagents client id/secret)
           -> SDK oboScopes exchange -> https://search.azure.com/.default

.NOTES
  Run AFTER `atk provision --env local` has created the Azure Bot resource.
  Azure CLI must be logged in to the same tenant (az login).
  Requires the `botservice` az extension (auto-installed on first use).

.EXAMPLE
  ./deploy/setup_bot_oauth.ps1 -BotName <bot-name> -ResourceGroup <rg>
#>
param(
    [Parameter(Mandatory = $true)] [string] $BotName,
    [Parameter(Mandatory = $true)] [string] $ResourceGroup,
    [string] $ConnectionName = "search-sso",
    [string] $FinAgentsClientId = "fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c",
    [string] $TenantId = "37f28838-9a79-4b20-a28a-c7d8a85e4eda",
    # Downstream scope obtained via OBO. The SDK oboScopes drives the final exchange;
    # keep this aligned with proxy config OBO_SCOPE.
    [string] $Scopes = "https://search.azure.com/.default",
    # finagents client secret. If omitted, read from backend/.env (AAD_CLIENT_SECRET).
    [string] $FinAgentsClientSecret
)

$ErrorActionPreference = "Stop"

if (-not $FinAgentsClientSecret) {
    $envPath = Join-Path $PSScriptRoot "..\backend\.env"
    if (Test-Path $envPath) {
        $line = Get-Content $envPath | Where-Object { $_ -match "^AAD_CLIENT_SECRET=" } | Select-Object -First 1
        if ($line) { $FinAgentsClientSecret = ($line -split "=", 2)[1].Trim() }
    }
}
if (-not $FinAgentsClientSecret) {
    throw "finagents client secret not provided and not found in backend/.env (AAD_CLIENT_SECRET)."
}

# Token Exchange URL must match manifest webApplicationInfo.resource (the finagents App ID URI).
$tokenExchangeUrl = "api://$FinAgentsClientId"

Write-Host "Creating OAuth connection '$ConnectionName' on bot '$BotName' (rg: $ResourceGroup)..." -ForegroundColor Cyan
Write-Host "  Provider : Azure Active Directory v2 (Aadv2)"
Write-Host "  App      : finagents ($FinAgentsClientId)"
Write-Host "  Scopes   : $Scopes"

az bot authsetting create `
    --resource-group $ResourceGroup `
    --name $BotName `
    --setting-name $ConnectionName `
    --client-id $FinAgentsClientId `
    --client-secret $FinAgentsClientSecret `
    --service Aadv2 `
    --provider-scope-string $Scopes `
    --parameters "clientId=$FinAgentsClientId" "clientSecret=$FinAgentsClientSecret" "tenantId=$TenantId" "tokenExchangeUrl=$tokenExchangeUrl" `
    --output table

Write-Host ""
Write-Host "Done. Next:" -ForegroundColor Green
Write-Host "  1. Ensure finagents has Application ID URI '$tokenExchangeUrl' and pre-authorizes the Teams client apps on 'access_as_user'."
Write-Host "  2. Ensure the manifest webApplicationInfo.resource = '$tokenExchangeUrl' (AAD_APP_CLIENT_ID=$FinAgentsClientId)."
Write-Host "  3. Run the proxy (npm run dev:teamsfx) and sideload appPackage/build/appPackage.local.zip into Teams."

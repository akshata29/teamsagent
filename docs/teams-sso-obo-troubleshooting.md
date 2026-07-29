# Teams SSO + On-Behalf-Of (OBO) troubleshooting — Option B

This document records the issues we hit getting **per-user Teams SSO + On-Behalf-Of (OBO)
token exchange** working for the Capital Markets Custom Engine Agent (Option B), and the exact
fixes applied to the app registration, Azure Bot resource, OAuth connection, and Teams manifest.

The end goal: a Teams user signs in silently via SSO, the proxy exchanges that token
On-Behalf-Of for an Azure AI Search token, and search results are trimmed to that user's
entitlements.

## Final working configuration (reference)

| Component | Setting | Value |
|---|---|---|
| App registration | Name / appId | `finagents` / `fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c` |
| App registration | Tenant | `37f28838-9a79-4b20-a28a-c7d8a85e4eda` (single-tenant) |
| App registration | Application ID URI (used for SSO) | `api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c` |
| App registration | Exposed scope | `access_as_user` |
| App registration | Web redirect URI | `https://token.botframework.com/.auth/web/redirect` |
| Azure Bot | Name / resource group | `capmarkets-obo-bot` / `astdataai` |
| Azure Bot | Messaging endpoint | `https://p6mx573x-3978.use.devtunnels.ms/api/messages` |
| OAuth connection | Name / provider | `search-sso` / Azure AD v2 (`Aadv2`) |
| OAuth connection | Token Exchange URL | `api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c` |
| OAuth connection | Scopes | `api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c/access_as_user` |
| Teams manifest | `webApplicationInfo.resource` | `api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c` |
| Teams manifest | `webApplicationInfo.id` | `fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c` |
| Proxy handler | OBO scopes (downstream) | `https://search.azure.com/.default` |

Key idea confirmed by the working run: the **SSO connection** authenticates the user against the
app's **own** identity, and the **downstream** `search.azure.com` scope is requested only on the
**OBO exchange** — never on the SSO connection itself.

## Timeline of issues and fixes

We hit three distinct failures in sequence. Each one masked the next, which is why it took several
iterations to reach a clean sign-in.

### Issue 1 — "Sign-in couldn't complete" (missing token redirect)

**Symptom.** The bot sent a sign-in card, but the exchange never started; sign-in failed generically.

**Root cause.** The `finagents` app registration had **no web redirect URI** for the Bot Framework
Token Service. The token service completes the OAuth handshake at a fixed redirect URL, and without
it the flow can't finish.

**Fix.** Added the redirect URI to the app registration:

```powershell
az ad app update --id fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c `
  --web-redirect-uris "https://token.botframework.com/.auth/web/redirect"
```

### Issue 2 — `resourcematchfailed` (the main blocker)

**Symptom.** SSO reached the token-exchange step and Teams returned an invoke
`signin/failure` with:

```
value: { code: 'resourcematchfailed', message: 'Resource match failed' }
```

**What `resourcematchfailed` means.** During silent SSO, Teams acquires a token for the resource in
the installed manifest's `webApplicationInfo.resource`, then compares that token's `aud` (audience)
claim against the OAuth connection's **Token Exchange URL**. If they don't match exactly, Teams
reports `resourcematchfailed`. Nothing about this is a "re-login" — the sign-in card is the silent
SSO handshake, not a visible prompt.

**Wrong turns we took (documented so we don't repeat them).** We first assumed it was a simple
string mismatch and tried aligning all three values to:

1. The **plain** form `api://fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c` — still failed.
2. The **domain-qualified** form `api://p6mx573x-3978.use.devtunnels.ms/fb3c0e70-...` — still failed.

We verified live that the installed manifest resource, the Token Exchange URL, and an app
identifier URI were byte-identical in the plain form, and it **still** failed. That proved the
token's `aud` was never the plain string, so string-matching alone could not work.

**Actual root cause.** This is a **standalone bot** (a bot only, no tab). Microsoft's bot-SSO
registration documentation is explicit:

> **Standalone bot**: enter the application ID URI as `api://botid-{YourBotId}`.

For a bot SSO token exchange, the token Teams mints has `aud = api://botid-{clientId}`. It is
**never** the plain `api://{clientId}` nor the domain-qualified `api://{domain}/{clientId}` form.
Because none of our three values used the required `botid-` prefix, the audience never matched the
Token Exchange URL.

**Fix.** Set all three to the `botid-` form: `api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c`.

1. Add the identifier URI to the app registration (keeping the existing URIs):

    ```powershell
    az ad app update --id fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c `
      --identifier-uris `
        "api://fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c" `
        "api://p6mx573x-3978.use.devtunnels.ms/fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c" `
        "api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c"
    ```

2. Set the OAuth connection's Token Exchange URL (see the recreate command under Issue 3 — the
   connection carries both the Token Exchange URL and the scope).

3. Change the manifest resource. In [proxy/appPackage/manifest.json](../proxy/appPackage/manifest.json)
   the source template was the cause — it produced the wrong resource:

    ```jsonc
    // before
    "resource": "api://${{BOT_DOMAIN}}/${{AAD_APP_CLIENT_ID}}"
    // after
    "resource": "api://botid-${{AAD_APP_CLIENT_ID}}"
    ```

**Reinstall required.** `webApplicationInfo.resource` is baked into the installed Teams package, so
after changing it the app must be **re-uploaded** in Teams (Apps → Manage your apps → Update, same
Teams app id). Azure-side changes take effect immediately; the manifest change only reaches Teams
via a re-sideload.

**Result.** The proxy log changed to `[handler:search] Successfully acquired token` and
`sign-in status=approved` — `resourcematchfailed` was gone.

### Issue 3 — OBO exchange error `-120592`

**Symptom.** SSO now succeeded, but the next step (exchanging the SSO token On-Behalf-Of for a
Search token) failed:

```
[OBO] exchangeToken failed: [-120592] - The current token for the 'search-sso' AzureBot connection
is not exchangeable for an on-behalf-of flow. Ensure the base token audience is for the bot/resource
app, such as an App ID URI like 'api://...' or otherwise includes the app's client id.
```

**Root cause.** The `search-sso` connection's **scope** was set to the downstream foreign resource
`https://search.azure.com/.default`. That made the SSO-exchanged base token carry
`aud = search.azure.com`. A token whose audience is a foreign resource **cannot** be used as an OBO
assertion — OBO requires a base token whose audience is your **own** app.

**Fix.** Re-scope the SSO connection to the app's **own** `access_as_user`, and keep the downstream
`search.azure.com` scope only on the OBO exchange (the proxy handler already requests it via
`oboScopes`). The Token Exchange URL stays on the working `botid-` value, so SSO is unaffected.

```powershell
$sec = ((Get-Content .\backend\.env |
  Where-Object { $_ -match '^AAD_CLIENT_SECRET=' } |
  Select-Object -First 1) -split '=',2)[1].Trim()

az bot authsetting delete -g astdataai -n capmarkets-obo-bot --setting-name search-sso

az bot authsetting create -g astdataai -n capmarkets-obo-bot --setting-name search-sso `
  --client-id fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c --client-secret $sec `
  --service Aadv2 `
  --provider-scope-string "api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c/access_as_user" `
  --parameters `
    clientId=fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c `
    "clientSecret=$sec" `
    tenantId=37f28838-9a79-4b20-a28a-c7d8a85e4eda `
    "tokenExchangeUrl=api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c"
```

For this OBO to succeed, `finagents` must hold **delegated permission to Azure AI Search**
(`user_impersonation`) with **admin consent** granted — which it does.

**Result.** SSO approves, the OBO exchange returns a Search token, and results are trimmed to the
signed-in user's entitlements.

## Summary of every change we made

### App registration (`finagents`, `fb3c0e70-...`)

- Added web redirect URI `https://token.botframework.com/.auth/web/redirect`.
- Added identifier URI `api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c` (the SSO audience for a
  standalone bot). The earlier plain and domain-qualified URIs were left in place but are not used
  by SSO.
- Confirmed the `access_as_user` scope is exposed and the Teams/M365 client app IDs are
  pre-authorized (unchanged from prior setup).

### Azure Bot OAuth connection (`search-sso`)

- Provider: Azure AD v2 (`Aadv2`).
- Token Exchange URL set to `api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c`.
- Scope changed **from** `https://search.azure.com/.default` (foreign resource — broke OBO) **to**
  `api://botid-fb3c0e70-f3bb-46a1-9f0b-2587b49a3d0c/access_as_user` (app's own identity —
  OBO-exchangeable).

### Teams manifest ([proxy/appPackage/manifest.json](../proxy/appPackage/manifest.json))

- `webApplicationInfo.resource` changed from `api://${{BOT_DOMAIN}}/${{AAD_APP_CLIENT_ID}}` to
  `api://botid-${{AAD_APP_CLIENT_ID}}`.
- Required a re-upload of the app package in Teams for the change to take effect.

### Proxy handler (unchanged, confirmed correct)

- `azureBotOAuthConnectionName = search-sso`.
- `oboScopes = ["https://search.azure.com/.default"]` — the downstream resource is requested on the
  OBO exchange, not on the SSO connection.

## Lessons learned

- **`resourcematchfailed` is an audience comparison**, not a login prompt. The check is: the `aud`
  of the token Teams mints (from the installed manifest's `webApplicationInfo.resource`) must equal
  the OAuth connection's Token Exchange URL.
- **A standalone bot requires the `api://botid-{clientId}` form** for the manifest resource,
  Token Exchange URL, and an app identifier URI. The plain and domain-qualified forms do not produce
  a matching token audience for bot SSO.
- **Separate the two token stages.** The SSO connection authenticates against the app's own
  identity (`access_as_user`); the downstream resource scope (`search.azure.com`) belongs on the OBO
  exchange. Putting the foreign resource on the SSO connection breaks OBO with `-120592`.
- **`webApplicationInfo.resource` is baked into the installed package** — changing it always
  requires re-uploading the Teams app; Azure-side changes do not.
- **Verify against live values, not assumptions.** String-matching the plain form looked correct on
  paper but still failed; only reading the authoritative doc revealed the required `botid-` prefix.

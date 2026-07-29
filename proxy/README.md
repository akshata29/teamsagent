# Option B — Custom Engine Agent proxy (Teams SSO + OBO)

This is the **Option B** integration: a **Custom Engine Agent (CEA)** built with the M365
Agents Toolkit + Agents SDK. It is the **trust boundary** for per-user document-level
security: `Teams SSO → On-Behalf-Of (Azure AI Search scope) → backend
/api/demo/optionB/invoke` (passing the user token in `x-ms-query-source-authorization`) →
Adaptive Card. The user token never leaves the proxy; the backend trims Azure AI Search
per user, then grounds the Foundry hosted agent. **Adaptive Cards are Option‑B only** (the
automatic Foundry Responses→Activity bridge in Option A preserves text only).

Key files: `src/agent.ts` (SSO + OBO `exchangeToken` + backend call), `src/cards.ts`
(Adaptive Cards), `src/config.ts` (`BACKEND_URL`, `AAD_OAUTH_CONNECTION_NAME`, `OBO_SCOPE`,
`DEMO_PERSONA_ID`), `appPackage/manifest.json` (CEA + `webApplicationInfo` SSO). Reuses the
existing **finagents** app (has the Azure AI Search delegated permission + admin consent).

## Run

Prereq: backend running on `http://localhost:8010` (`run_backend.bat`, live Azure).

```powershell
npm install ; npm run build
# A) Agents Playground (no tenant / no SSO — tests cards + backend bridge):
npm run dev:teamsfx:launch-playground
# B) Real Teams SSO + OBO end-to-end:
#   1. devtunnel host -p 3978 --allow-anonymous
#   2. npx -y --package @microsoft/m365agentstoolkit-cli atk provision --env local
#   3. Create an Azure Bot OAuth connection "search-sso" using finagents (AAD v2;
#      scopes access_as_user + https://search.azure.com/.default)
#   4. npm run dev, then sideload appPackage/build/appPackage.local.zip into Teams
```

Provision/publish to a tenant (also surfaces in M365 Copilot):
`atk provision|deploy|publish --env dev` (publish needs M365 admin approval; not in GCC).

---

<details>
<summary>Scaffold reference (original template docs)</summary>

## Overview of the Basic Custom Engine Agent template

This app template is built on top of [Microsoft 365 Agents SDK](https://github.com/Microsoft/Agents).
It showcases an agent that responds to user questions like ChatGPT. This enables your users to talk with the agent using your custome engine.

## Get started with the template

> **Prerequisites**
>
> To run the template in your local dev machine, you will need:
>
> - [Node.js](https://nodejs.org/), supported versions: 22.
> - [Microsoft 365 Agents Toolkit Visual Studio Code Extension](https://aka.ms/teams-toolkit) latest version or [Microsoft 365 Agents Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli).
> - Prepare your own [Azure OpenAI](https://aka.ms/oai/access) resource.

> For local debugging using Microsoft 365 Agents Toolkit CLI, you need to do some extra steps described in [Set up your Microsoft 365 Agents Toolkit CLI for local debugging](https://aka.ms/teamsfx-cli-debugging).

1. First, select the Microsoft 365 Agents Toolkit icon on the left in the VS Code toolbar.
1. In file *env/.env.playground.user*, fill in your Azure OpenAI key `SECRET_AZURE_OPENAI_API_KEY=<your-key>`, endpoint `AZURE_OPENAI_ENDPOINT=<your-endpoint>`, and deployment name `AZURE_OPENAI_DEPLOYMENT_NAME=<your-deployment>`.
1. Press F5 to start debugging which launches your agent in Microsoft 365 Agents Playground using a web browser. Select `Debug in Microsoft 365 Agents Playground`.
1. You can send any message to get a response from the agent.

**Congratulations**! You are running an agent that can now interact with users in Microsoft 365 Agents Playground:

![Basic AI Agent](https://github.com/user-attachments/assets/984af126-222b-4c98-9578-0744790b103a)

## What's included in the template

| Folder       | Contents                                            |
| - | - |
| `.vscode`    | VSCode files for debugging                          |
| `appPackage` | Templates for the application manifest        |
| `env`        | Environment files                                   |
| `infra`      | Templates for provisioning Azure resources          |
| `src`        | The source code for the application                 |

The following files can be customized and demonstrate an example implementation to get you started.

| File                                 | Contents                                           |
| - | - |
|`src/index.ts`| Sets up the agent server.|
|`src/adapter.ts`| Sets up the agent adapter.|
|`src/config.ts`| Defines the environment variables.|
|`src/agent.ts`| Handles business logics for the Basic Custom Engine Agent.|

The following are Microsoft 365 Agents Toolkit specific project files. You can [visit a complete guide on Github](https://github.com/OfficeDev/TeamsFx/wiki/Teams-Toolkit-Visual-Studio-Code-v5-Guide#overview) to understand how Microsoft 365 Agents Toolkit works.

| File                                 | Contents                                           |
| - | - |
|`m365agents.yml`|This is the main Microsoft 365 Agents Toolkit project file. The project file defines two primary things:  Properties and configuration Stage definitions. |
|`m365agents.local.yml`|This overrides `m365agents.yml` with actions that enable local execution and debugging.|
|`m365agents.playground.yml`| This overrides `m365agents.yml` with actions that enable local execution and debugging in Microsoft 365 Agents Playground.|

## Additional information and references

- [Microsoft 365 Agents Toolkit Documentations](https://docs.microsoft.com/microsoftteams/platform/toolkit/teams-toolkit-fundamentals)
- [Microsoft 365 Agents Toolkit CLI](https://aka.ms/teamsfx-toolkit-cli)
- [Microsoft 365 Agents Toolkit Samples](https://github.com/OfficeDev/TeamsFx-Samples)

## Known issue
- The agent is currently not working in any Teams group chats or Teams channels when the stream response is enabled.

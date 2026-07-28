# Capital Markets Foundry Hosted Agent on Teams — Option A + Option B MVP

A demo that showcases **two ways to expose a Microsoft Foundry hosted agent in Microsoft
Teams / M365 Copilot**, side by side, for a **Capital Markets** research desk — with
**document-level security** enforced via **On-Behalf-Of (OBO)** identity passthrough.

- **Option A — Direct Foundry publish.** The hosted agent is published to Teams via Azure
  Bot Service. Its in-container Search tool runs **app-only** (the hosting gateway strips the
  user token), so results are an *undifferentiated* slice.
- **Option B — M365 Agents SDK proxy.** A Custom Engine Agent is the **trust boundary**:
  Teams SSO → OBO → **per-user** Azure AI Search trimming → grounding injected into the hosted
  agent. Real document-level security.

> The two customer requirements — a **hosted** agent *and* an **OBO tool inside the agent** —
> are mutually exclusive today (the gateway strips the user token, and `agent_reference`
> strips inline tools). The demo turns this into the teaching point. See
> `.copilot-tracking/research/2026-07-28/capmarkets-teams-agent-mvp-research.md`.

## What you can do in the UI

Pick a persona (Equity Research Analyst / Fixed-Income PM / Compliance Officer), ask a research
question, and **run both options at once**. The compare view + document-access map show, per
document, what Option A exposed vs what Option B correctly trimmed for that user.

## Why Option A is app-only (and Option B does per-user OBO)

Signing in in the UI gives **your FastAPI backend** a user token — not the hosted agent
container. That distinction is the whole point of the two options:

- **Option A — Direct Foundry/Bot-Service publish.** Retrieval happens *inside the deployed
  agent's own tool* ([agent/tools/search_tool.py](agent/tools/search_tool.py)). Per-user OBO is
  **structurally impossible** here for two independent reasons:
  1. **The hosted-agent runtime gateway strips inbound credentials.** The platform terminates
     TLS and injects only its own `FOUNDRY_*` env vars; the caller's `Authorization` bearer never
     reaches the container. So the tool has no user assertion to exchange and authenticates with
     `DefaultAzureCredential()` = the **agent's managed identity** ("app-only identity").
  2. **Direct Teams publish (Bot Service) never yields an OBO-exchangeable user token** — the
     inbound channel JWT is a channel/authorization token, not an Entra *user* token. Only the
     `Entra` auth scheme (the proxy path) derives an exchangeable user identity.

  The platform does pass a per-user **isolation key** (`has_user_id=True`, `x-ms-user-identity`),
  but that is an *opaque session-isolation identifier, not an OBO token* — it can't trim Search
  per document by itself.

- **Option B — M365 Agents SDK proxy (Custom Engine Agent).** The proxy **is** the trust
  boundary: `Teams SSO → MSAL OBO → Search-scoped user token → AI Search query with
  x-ms-query-source-authorization (trimmed to that user) → results injected as grounding into the
  hosted agent`. The user token still never enters the container; the **proxy** does the trimming.

**Takeaway:** per-user document security in a Teams-published agent requires the Option B proxy
pattern. The OBO token must be presented from a trust boundary (proxy/backend) — never from the
in-container tool.

## Layout

| Path | What |
|---|---|
| `backend/` | FastAPI demo backend (personas, Option A/B/compare, audit, settings) |
| `agent/` | Foundry **hosted agent** container (Agent Framework + app-only Search tool) |
| `deploy/` | Index creation, synthetic seeding, hosted-agent deploy, Option A Teams publish |
| `frontend/` | React 18 + Vite + Tailwind demo UI (Demo, Workflow, Architecture, Settings) |
| `proxy/` | Option B **M365 Agents SDK** Custom Engine Agent (Teams SSO + OBO) |

## Run the demo (offline — no Azure required)

The backend runs fully offline against a synthetic Capital Markets corpus, so the whole demo
works before any Azure wiring.

```powershell
run_all.bat
```

- Backend: http://localhost:8010/api/health
- Frontend: http://localhost:5174

Or individually: `run_backend.bat` and `run_frontend.bat`.

## Wire up Azure (live mode)

1. Copy `backend/.env.example` → `backend/.env` and fill in Foundry, Azure AI Search, Entra
   (OBO app registration with delegated `https://search.azure.com/.default` + admin consent),
   and Azure OpenAI. Set `OFFLINE_MODE=false`.
2. Build the index + seed synthetic data:
   ```powershell
   pip install -r deploy/requirements.txt
   python -m deploy.create_index
   python -m deploy.seed_synthetic_data
   ```
3. Build/push the agent image and deploy the hosted agent:
   ```powershell
   # Cloud build (no local Docker needed); guarantees linux/amd64:
   az acr build --registry <registry> --image capmarkets-agent:v1 --platform linux/amd64 agent/
   $env:AGENT_IMAGE="<registry>.azurecr.io/capmarkets-agent:v1"
   python -m deploy.deploy_hosted_agent
   ```
   Then invoke via the agent's **dedicated endpoint**
   (`project.get_openai_client(agent_name=...).responses.create(...)`), never `agent_reference`.
   See **Hosted-agent deployment contract** below for the required protocol/model/RBAC settings.
4. **Option A** — publish to Teams:
   ```powershell
   az provider register --namespace Microsoft.BotService
   az deployment group create -g <rg> -f deploy/bicep/botservice.bicep -p botName=capmarkets-bot msaAppId=<app-id> agentActivityEndpoint=<agent activityProtocol url>
   python -m deploy.publish_teams_optionA
   ```
   RBAC: **Foundry User** + **Azure Bot Service Contributor**. Tenant scope needs **M365 admin approval**.
5. **Option B** — proxy (see `proxy/README.md`): `atk provision/deploy/publish`. No GCC publish.

## Validate

```powershell
cd backend; .\.venv\Scripts\Activate.ps1; pytest -q      # backend tests
cd ..\frontend; npm run build                            # frontend build
```

## Notes

- All corpus content is **synthetic**; no real market data or MNPI.
- Azure AI Search native ACL trimming uses `2026-05-01-preview` (`azure-search-documents==12.1.0b1`);
  a GA `search.in()` security-trimming fallback is included (`USE_NATIVE_ACL=false`).
- Tokens are never logged; every invocation is audited (`backend/audit_log.jsonl`).

## Hosted-agent deployment contract (Foundry)

Deploying the container to Foundry Agent Service has a strict runtime contract. These are the
non-obvious requirements that make the difference between "Status: N/A" and a live agent:

- **Container contract** ([Learn](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agent-contract)):
  listen on **port 8088**, serve `GET /readiness` → `200`, and `POST /responses`. Use the SDK
  adapter so these register automatically — in Python the package is the top-level
  `agent_framework_foundry_hosting` (underscores), served via
  `ResponsesHostServer(agent).run(host="0.0.0.0", port=int(os.environ.get("PORT", "8088")))`.
  (There is **no** `agent_framework.foundry.hosting.serve`.)
- **`FoundryChatClient` requires a credential:** `FoundryChatClient(project_endpoint=..., model=...,
  credential=DefaultAzureCredential())` — the container runs as the platform-created agent identity.
- **Declare the protocol version.** `create_version` must pass
  `protocol_versions=[ProtocolVersionRecord(protocol=AgentEndpointProtocol.RESPONSES, version="2.0.0")]`.
  Without it the version reports `active` but no container provisions; the installed hosting package
  requires **`2.0.0`** (older docs show `1.0.0`). A correct deploy transitions `CREATING → ACTIVE`
  in under a minute — `Status: N/A` / "not in Running state" for minutes means a failed provision.
- **Model must support encrypted reasoning content.** The agent-framework Responses path adds
  `include=["reasoning.encrypted_content"]` on stateless calls, which **gpt-4o rejects**
  (`400 Encrypted content is not supported with this model`). Use a GPT-5 or reasoning model
  (e.g. `chat5nano`, `chato4mini`, `chato1`). Set via `AGENT_MODEL_DEPLOYMENT` (default `chat5nano`
  in `deploy/deploy_hosted_agent.py`); the reserved `FOUNDRY_*` env prefix is auto-injected.
- **Invoke via the dedicated agent endpoint:** `project.get_openai_client(agent_name=<name>)`
  → `.responses.create(input=...)`. The shared `agent_reference` path returns
  `400 Hosted agents can only be called through the agent endpoint`.
- **RBAC** (the tooling assigns these automatically with `azd`; do it manually otherwise):
  **Container Registry Repository Reader** (image pull) on the project + agent identities;
  **Cognitive Services OpenAI User** (model calls) on the Foundry account for the agent instance
  identity; **Search Index Data Reader** for the in-container tool. Note there are **two** agent
  identities — the `instance_identity` (what the container runs as) and the `blueprint`
  (provisioning) identity — grant both.
- **Diagnostics without azd/Docker:** exec inside the image in the cloud with
  `az acr run --registry <reg> --cmd "<image> python -c '<probe>'" /dev/null`; stream live container
  logs via `project.agents.get_session_log_stream(agent_name, agent_version, session_id)` (session id
  field is `agent_session_id`; events are SSE `event: log` / `data: {json}`).

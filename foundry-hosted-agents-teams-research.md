<!-- markdownlint-disable-file -->
# Task Research: Exposing Microsoft Foundry Hosted Agents on Microsoft Teams

> Retrieval date for all version/availability claims: **2026-07-27** (Microsoft Learn).
> Availability (GA vs Preview) changes frequently — re-verify before a production go/no-go.
>
> **Citation convention:** every factual claim carries an inline `[n]` marker that maps to a
> numbered source in [References](#references). Claims marked `[inf]` are analyst inference from
> the cited facts (not a direct doc statement) and are flagged so you can challenge them.

## Task Description

Customer is heavily invested in Microsoft Foundry, running a **Standard** setup and
provisioning **multiple Foundry resources**, segmented per **line of business (LOB)** and
application team. They receive many requests to **expose hosted agents in Microsoft Teams**.
They need guidance, best practices, and explicit **Preview vs GA** callouts for each path.

## Scope and Success Criteria

- Scope: Options and best practices to surface Foundry **hosted agents** (and prompt agents) in
  Microsoft Teams (and Microsoft 365 Copilot, which shares the same publish pipe) [1]. Governance
  for a multi-resource, per-LOB topology. Identity, RBAC, networking, observability, lifecycle.
- Out of scope: Building the agent logic itself; non-Teams channels beyond brief mention.
- Assumptions:
  - "Standard setup" = new **Microsoft Foundry** portal (GA) with the account + project resource
    model [7]. `[inf]`
  - Capital Markets / Banking / Insurance LOBs → regulated data, so governance is first-class. `[inf]`
- Success Criteria:
  - Each integration path is labeled **GA** or **Preview** with a cited source.
  - Best practices are concrete and mapped to the per-LOB multi-resource topology.

## TL;DR — Availability at a glance (verified 2026-07-27)

| Capability | Status | Source |
|---|---|---|
| Microsoft Foundry portal (new) | **GA** | [7] |
| Foundry **Hosted Agents** (managed hosting service) | **GA** | [3][4] |
| Publish Foundry agent → **Teams & M365 Copilot** (portal + REST) | **GA** ("the generally available publish flow") | [1] |
| Responses → **Activity protocol** bridge for Teams delivery | **GA** (automatic, no extra wiring) | [3] |
| **M365 Agents Toolkit / M365 Agents SDK** custom-engine-agent proxy path | **GA** tooling (Teams Toolkit successor) | [8][9] |
| **Copilot Studio** → Teams channel wrapper | **GA** | [11] |
| **A2A** (agent-to-agent) endpoint protocol | **Preview** | [5] |
| **MCP** endpoint protocol on the agent | **Preview** | [5] |
| Python `agent-framework-foundry-hosting` integration package | **Preview / prerelease** (service is GA) | [4] |
| `FoundryAgent` service-managed sessions (`allow_preview=True`) | **Preview** surface | [6] |
| M365 Agents Toolkit publishing in **GCC/Government** tenants | **Not supported** | [10] |
| Hosted-agent **private ACR** (network isolation) | Only for projects created **after 2026-06-25**; earlier projects need public registry access | [7] |

Bottom line `[inf]`: the **primary, recommended path is GA** — publish a Foundry agent directly to
Teams/M365 Copilot [1]. The pieces that are still **Preview** are the newer *protocol* surfaces
(A2A, MCP) [5] and some Python hosting glue [4][6], not the core Teams publishing experience [1].

## Integration Options

### Option A — Publish the Foundry agent directly to Teams (RECOMMENDED default) — **GA** [1]

How it works: In the Foundry portal (or via REST) select **Publish → Teams and Microsoft 365
Copilot** [1]. Foundry:
- Provisions/uses an **Azure Bot Service** resource that proxies messages between the Microsoft
  channel adapters (Teams, Copilot) and the agent's **Activity Protocol** endpoint [1][2].
- Enables the `activity` protocol on the agent and compiles a **Teams app manifest** (`.zip`),
  then submits it to the M365 Copilot/Teams agent catalogs [1].
- Sets an authorization scheme (`BotServiceRbac` or `BotServiceTenant`) based on scope [1][5].

What gets published is the agent's **stable endpoint**, so you roll out new agent versions
behind it without republishing [1]. For **hosted agents** specifically, when the agent logic uses
the **Responses** protocol, the platform **automatically bridges Responses → Activity** for
channel delivery — no separate wiring [3].

Publish scope (controls visibility + who can call) [1]:
- **Just you** / `Shared`: enables `BotServiceRbac`, no admin approval; participants who have the
  required Foundry permissions on the project can use it [1].
- **People in your organization** / `Tenant`: enables `BotServiceTenant`, requires **M365 admin
  approval** in the Microsoft 365 admin center; then discoverable under "Built by your org" [1].

Prerequisites (verified) [1]:
- **Foundry User** role on the project (create/manage/publish agents); the Foundry RBAC roles were
  renamed from Azure AI User/Owner/etc. with role IDs unchanged [1].
- **Azure Bot Service Contributor Role** (`Microsoft.BotService/botServices/write` +
  `.../channels/write`) on the target resource group — **Foundry roles do NOT grant this** [1][12].
- `Microsoft.BotService` resource provider registered [1].

Preview caveat inside a GA flow: the activity-protocol endpoint URL still carries an
`api-version=2025-05-15-preview` query string [2], but the **publish feature itself is GA** — the
docs state the "generally available publish flow", and older "agent application" format agents
must be **upgraded to the new agent model** to publish [1].

Best for `[inf]`: fastest, lowest-glue, keeps agent + versioning + tracing in Foundry.

### Option B — Custom Engine Agent proxy via M365 Agents Toolkit / M365 Agents SDK — **GA tooling** [8][9]

How it works: Build a **proxy app** (a Custom Engine Agent / bot) with the **Microsoft 365
Agents Toolkit** (the evolution of Teams Toolkit) [9] + **M365 Agents SDK**, and have it call the
Foundry agent as its backend brain [8]. The SDK is model-/orchestrator-agnostic (Foundry,
Semantic Kernel, LangChain, etc.) and targets multiple channels [10][15]. This path enables
"advanced customization, debugging, and multi-environment deployment" and scenarios "requiring
custom logic, SSO, or managed infrastructure" [8].

Trade-offs & caveats:
- More code and infra to own vs Option A [8]. `[inf]`
- Toolkit templates: the Agents SDK project flow currently "works for JavaScript and TypeScript
  only. Support is planned for Python." [8-adjacent, create-new-toolkit-project] — see [8] family;
  documented as JS/TS today, Python planned [10]. `[inf on exact template scope]`
- **Publishing via the Agents Toolkit is NOT supported in Microsoft 365 Government tenants** [10].
- Local testing: **Microsoft 365 Agents Playground** removes the need for a dev tenant/tunnel [9].
- Ships built-in **SSO**, data storage, serverless functions, and **CI/CD for GitHub & Azure
  DevOps** [9].

Best for `[inf]`: teams needing rich Teams-native UX, custom SSO/OBO, or logic beyond the agent.

### Option C — Copilot Studio wrapper — **GA** [11]

How it works: Surface the agent through **Copilot Studio**, then add the **Microsoft 365 and
Microsoft Teams** channel [11]. It's a fully managed low-code SaaS with built-in compliance via
Power Platform and admin-approval publishing [8][11]. Sharing with the whole organization requires
admin approval [11].

Best for `[inf]`: business/low-code owners; centralized Power Platform governance. Weaker fit when
you want to preserve Foundry-native orchestration/observability end to end.

### Option D — Newer protocol surfaces (A2A / MCP) — **Preview** [5]

Foundry agents can also expose **A2A** (agent-to-agent delegation) and **MCP** endpoints; the
agent object model lists both explicitly as **(preview)** [5]. Relevant if another
agent/orchestrator (not the Teams client directly) consumes the agent [5]. `[inf]` Do **not** put
these on a production Teams critical path yet.

## Detailed option comparison matrix (all aspects)

Legend: ✅ strong / native · 🟡 partial or needs work · ❌ not supported / heavy lift.
Options: **A** = Direct Foundry publish · **B** = M365 Agents Toolkit/SDK proxy (Custom Engine
Agent) · **C** = Copilot Studio wrapper · **D** = A2A/MCP protocol surface. Cells cite the source
for the underlying fact; the ✅/🟡/❌ rating is analyst judgement `[inf]` unless a doc states it.

| Aspect | A — Direct publish | B — Agents Toolkit/SDK proxy | C — Copilot Studio | D — A2A/MCP protocol |
|---|---|---|---|---|
| **Availability (GA/Preview)** | ✅ **GA** publish flow [1] | ✅ **GA** tooling [8][9] | ✅ **GA** [11] | ❌ **Preview** protocols [5] |
| **Reuse of existing Foundry agent** | ✅ Publishes the agent as-is via stable endpoint [1] | ✅ Calls the Foundry agent as backend brain [8] | 🟡 Wraps via connector/action, or re-does topics [8][11] `[inf]` | ✅ Exposes agent over A2A/MCP to a consumer [5] |
| **Teams UX richness (Adaptive Cards, streaming, citations)** | 🟡 Platform-standard chat; Responses→Activity auto-bridge [3] `[inf]` | ✅ Full control (advanced customization) [8] | 🟡 Copilot Studio card set; less code control [8] `[inf]` | 🟡 Depends on the consuming client [5] `[inf]` |
| **Human-in-the-loop gates** | 🟡 Implement inside agent logic `[inf]` | ✅ Custom logic in the bot [8] `[inf]` | 🟡 Topic-level gating `[inf]` | 🟡 In consumer `[inf]` |
| **Development effort** | ✅ Lowest — portal/REST publish, minimal code [1][8] | ❌ Highest — build/host a bot app + CI/CD [8][9] | ✅ Low-code managed SaaS [8] | 🟡 Enable endpoint + build/consume client [5] `[inf]` |
| **Tracing (end-to-end)** | ✅ Agent runs in Foundry with end-to-end tracing [3][13] | 🟡 Two hops (bot + Foundry); stitch traces yourself `[inf]` | 🟡 Power Platform analytics + Foundry backend only `[inf]` | 🟡 Agent-side traced; consumer separate `[inf]` |
| **Observability / Continuous evaluation** | ✅ Foundry enterprise observability/eval on the deployed agent [7][13] | 🟡 Bot calls may bypass Foundry eval trigger; use trace eval `[inf]` | 🟡 Copilot Studio analytics; Foundry eval only on backend calls `[inf]` | 🟡 Trace eval over App Insights `[inf]` |
| **Identity / SSO** | ✅ Dedicated **Entra agent identity** auto-created at deploy [3][13]; Bot Service channel auth [1][5] | ✅ Toolkit provides simplified **SSO** [9]; OBO passthrough supported by agent identity [13] | 🟡 Power Platform/maker identity + connector auth [8] `[inf]` | 🟡 Entra auth on agent endpoint [5] |
| **RBAC** | ✅ Foundry User (publish) + Foundry Agent Consumer (invoke) at agent scope + Azure Bot Service Contributor for infra [1][5][12] | ✅ App RBAC + Foundry role for backend calls `[inf]` | 🟡 Power Platform env roles + connector perms [8] `[inf]` | ✅ Entra role (e.g., Foundry Agent Consumer) at agent scope [5] |
| **Managed identity** | ✅ Per-agent system-assigned Entra identity for scoped downstream (models/tools/MCP) [3][13] | ✅ App can use its own MI + agent MI on backend [13] `[inf]` | 🟡 Connector-based; less direct MI control [8] `[inf]` | ✅ Agent MI [13] |
| **Private endpoint / network isolation** | 🟡 Portal publish blocked when public access disabled → use **REST/VNet publish path** [1][2]; Traces & Workflow Agents not fully isolation-ready; private ACR only for projects created after 2026-06-25 [7] | 🟡 You control app networking; backend bound by Foundry VNet limits [7] `[inf]` | ❌ SaaS — least private-networking control [8] `[inf]` | 🟡 Bound by Foundry VNet limits [7] `[inf]` |
| **Admin governance / approval** | ✅ Tenant scope → **M365 admin center** approval + agent store listing [1] | 🟡 Publish via Teams/store submission [8] `[inf]` | ✅ Org sharing requires admin approval; Power Platform governance [8][11] | ❌ No Teams store gate (dev-controlled) [5] `[inf]` |
| **Data residency / compliance** | 🟡 Response data flows into M365/Teams under M365 terms — review per LOB [1] | 🟡 You host the app → control data path (+M365 for channel) [8] `[inf]` | 🟡 Power Platform + M365 data handling [8] `[inf]` | ✅ Stays in your control until a consumer calls it [5] `[inf]` |
| **CI/CD** | 🟡 REST publish scriptable [2]; version selector for rollout [1] | ✅ Toolkit ships GitHub/Azure DevOps CI/CD [9] | 🟡 Solution import/export (ALM) [8] `[inf]` | 🟡 Custom `[inf]` |
| **Versioning / rollout** | ✅ Stable endpoint + version selector (pin or "always latest"); no republish [1] | 🟡 App deploy + backend version selector [1] `[inf]` | 🟡 Copilot Studio publish versions [11] `[inf]` | 🟡 Agent version indicator [6] `[inf]` |
| **Multi-channel reach beyond Teams** | 🟡 Teams + M365 Copilot [1] | ✅ Teams, M365 Copilot, Web, Email, SMS, +more channels [9][15] | 🟡 Teams + M365 + web [11] `[inf]` | 🟡 Any A2A/MCP consumer [5] `[inf]` |
| **Government / GCC support** | ✅ Direct publish path available [1] `[inf]` | ❌ Agents Toolkit publishing **not supported** in M365 Government [10] | 🟡 Verify per feature [8] `[inf]` | 🟡 Verify per feature `[inf]` |
| **Licensing / cost drivers** | Foundry model/hosting tokens [3] + Azure Bot Service resource [1] | Foundry [8] + app hosting + Bot Service [1] `[inf]` | Copilot Studio + Power Platform licensing [8] `[inf]` | Foundry only [5] `[inf]` |
| **Maintainability** | ✅ Least surface to own [1][8] `[inf]` | ❌ Own an app + infra lifecycle [8] `[inf]` | ✅ Managed SaaS [8] | 🟡 Own client + endpoint [5] `[inf]` |
| **Multi-LOB fit (per-resource topology)** | ✅ Publish per project; Bot Service + RBAC roll up per LOB [1] `[inf]` | 🟡 One app per LOB or multi-tenant app design [8] `[inf]` | 🟡 Per-environment governance [8] `[inf]` | 🟡 Per agent [5] `[inf]` |
| **Time to demo** | ✅ Fastest (minimal code) [8] `[inf]` | ❌ Slowest (build + host) [8] `[inf]` | ✅ Fast (low-code) [8] `[inf]` | 🟡 Medium `[inf]` |

### How to read the matrix `[inf]`
- **Option A wins on**: availability (GA) [1], effort [8], Foundry-native tracing/observability
  [3][13], agent identity/RBAC [1][5][13], governance [1], and multi-LOB roll-up. Default for most
  requests.
- **Option B wins on**: UX richness/customization [8], SSO/CI-CD [9], and multi-channel reach
  [9][15] — at the cost of building/operating an app and **no GCC publish** [10].
- **Option C wins on**: low-code speed and Power Platform governance [8][11] — at the cost of
  weaker Foundry-native tracing/eval and private-networking control [8].
- **Option D** is a **Preview** integration primitive [5], not a Teams-client experience — use it
  for agent-to-agent / MCP consumption, not the production Teams critical path yet.

## UX & Identity deep dive: what Option A gives vs. what requires Option B

A common question is whether **Option A (direct publish) loses Teams-native UX and custom SSO/OBO**.
The accurate answer is *partly* — you keep conversational chat, but lose the authored-UI and
customer-controlled identity flows.

### Teams UX
- Direct publish exposes the agent over the **Activity Protocol** — the Bot Framework protocol
  Teams renders natively — so the agent is a real conversational bot with **Markdown text** [16],
  and Foundry auto-bridges Responses → Activity for hosted agents [3].
- **Inline citations** (footnote-style `[1]`, `[2]` with source title/abstract/URL on hover) are a
  Teams client capability for AI-generated bot messages and render without a custom app [17].
- What direct publish does **not** give you, because Foundry bridges the agent's **text response**
  only `[inf]`: authoring **Adaptive Cards** (multi-column, image banners, `Action.Execute`
  buttons) [18], **clarification cards**, **suggested-prompt chips**, and **thumbs-up/down
  feedback** controls [18], and Teams surfaces like **message extensions, tabs, and
  dialogs/Stageview** [18]. Those are built with the Teams SDK / M365 Agents SDK (Option B) [18].

| Teams capability | A — Direct publish | Needs B — Agents SDK/Toolkit |
|---|---|---|
| Conversational chat + Markdown | ✅ [16] | — |
| Inline footnote citations | ✅ [17] | — |
| Authored Adaptive Cards (buttons, columns) | ❌ `[inf]` | ✅ [18] |
| Clarification cards, suggested prompts, feedback | ❌ `[inf]` | ✅ [18] |
| Message extensions, tabs, dialogs/Stageview | ❌ `[inf]` | ✅ [18] |

### Identity / SSO / OBO
- Direct publish provides **channel-level auth** — `BotServiceRbac` or `BotServiceTenant` control
  *who can call* the agent [1][5] — and every hosted agent gets a **dedicated Entra agent
  identity** for scoped **unattended (app-only)** downstream access [3][13][19].
- **Per-user OBO (attended flow)** — acting on downstream resources *as the signed-in user* —
  requires an **application that first authenticates the user and passes the user token to Agent
  Service**, which then exchanges it for an agent-identity + delegated-permission token [19][20].
- The documented per-user delegation paths — a trusted service sending the `x-ms-user-identity`
  header (with the `UserIdentityImpersonation/action` permission), or `Microsoft.Identity.Web`
  performing the OBO exchange — are explicitly **"your service is the trust boundary"** patterns,
  i.e., the app you build in Option B (or an A2A OBO caller) [20][21][5].
- Conclusion `[inf]`: direct publish alone does **not** give a customer-controlled OBO/SSO to
  downstream resources on behalf of the Teams user. If per-user OBO is required, use **Option B**
  (Agents SDK proxy calling the Foundry agent) or a hybrid.

### Practical guidance `[inf]`
- **Internal Q&A / research agents** → Option A is sufficient (chat + citations + service-side
  agent identity for downstream) [16][17][3][13].
- **Custom cards / approval-button HITL / per-user OBO** → Option B [18][20], reserved for the
  subset of LOB agents that need it.
- **Hybrid** is common: default LOB agents on Option A; high-touch agents (e.g., trade-approval
  needing per-user Graph/OBO + rich cards) on Option B.

## Recommended approach for this customer `[inf]`

**Default to Option A (GA direct publish)** [1] for the bulk of LOB agent requests; reserve
**Option B** [8] for the subset needing bespoke Teams UX / SSO-OBO / non-Foundry orchestration.
Rationale: Option A is GA [1], minimizes glue [8], preserves Foundry versioning/observability
[1][13], and the Activity bridge is automatic for hosted agents [3].

## Best practices for a multi-Foundry-resource, per-LOB Standard setup

### Topology & isolation
- Keep the **Azure Bot Service** resource for each published agent in that LOB's resource group so
  RBAC and cost roll up per LOB [1]. `[inf on the per-LOB grouping recommendation]`
- Stable-endpoint + **version selector** ("Always use latest" vs pinned) is the release control —
  publish once, roll versions behind it [1]. `[inf]` Pin versions for regulated LOBs that require
  change control; use "Always use latest" only where auto-rollout is acceptable [1].

### Identity, RBAC & least privilege
- Separate **publish** permissions from **invoke** permissions; **Foundry roles do not grant** the
  Bot Service permissions needed to publish, so grant **Azure Bot Service Contributor** only to
  whoever runs the publish [1][12].
- Choose the publish scope deliberately: **Tenant** scope routes through **M365 admin approval**,
  so make that approval step part of each LOB's release checklist [1].
- Each hosted agent gets its own **dedicated Entra agent identity** automatically — use it for
  scoped downstream access (models, tools, MCP) instead of shared secrets; OBO passthrough is
  supported when configured [3][13].
- Auth schemes are set by the publish flow: `BotServiceRbac` (Just you) or `BotServiceTenant`
  (org) [1][5]. For non-Teams programmatic callers, use `Entra` with the **Foundry Agent Consumer**
  role at agent scope for tighter isolation than project-wide sharing [5].

### Networking (regulated LOBs)
- Projects that **disable public network access** can't publish from the portal — use the
  **REST publish path** (Bot Service with public access disabled + private DNS/reverse proxy) [1][2].
- Know the gaps: some features (**Traces**, **Workflow Agents**) don't yet fully support network
  isolation, and hosted-agent **private ACR** works only for projects created **after 2026-06-25**
  (earlier projects need public registry access) [7].

### Observability & governance (financial services)
- Publishing processes/stores agent metadata AND **response data** in M365/Teams, subject to those
  services' compliance, **data residency**, and handling terms — evaluate per LOB before Tenant
  rollout (explicit Learn warning) [1].
- Keep **human-in-the-loop** gates, PII masking, and risk disclaimers in the agent/orchestrator
  layer — the Teams channel does not add these. `[inf]`
- Preserve end-to-end **tracing/continuous evaluation** in Foundry: Option A keeps the agent in
  Foundry (native telemetry) [3][13]; Option B/C may break the chain — validate telemetry per
  path. `[inf]`

### Lifecycle & operations
- To update **metadata** in Teams, use "Update agent Teams and Microsoft 365 Copilot display
  properties" (auto-increments version); to update **behavior**, roll the agent version behind the
  stable endpoint — no republish needed [1].
- Government/GCC: direct Foundry publish is the path [1] `[inf]`; **Agents Toolkit publishing is
  unsupported** in M365 Government [10].

## Open Questions for Planning `[inf]`

1. Are any LOB projects created **before 2026-06-25** and requiring private networking (private
   ACR limitation) [7]?
2. Which LOBs are **GCC/Government** (rules out Agents Toolkit publishing) [10]?
3. Data residency: is exporting agent **response data** into M365/Teams approved per LOB [1]?
4. Version policy per LOB: "Always use latest" vs pinned (change-control requirements) [1]?
5. Which agents genuinely need **Option B** (custom UX/SSO-OBO) [8] vs default **Option A** [1]?

## References

All URLs are Microsoft Learn, retrieved **2026-07-27**.

1. Publish agents to Microsoft 365 Copilot and Microsoft Teams in the Foundry portal (GA publish
   flow, prerequisites, scopes, Bot Service, Activity protocol, version selector, metadata update,
   data-flow warning) — https://learn.microsoft.com/azure/foundry/agents/how-to/publish-copilot
2. Publish agents to Microsoft 365 Copilot and Microsoft Teams by using the REST API + VNet
   guidance (private-network path; activity-protocol endpoint `api-version=2025-05-15-preview`) —
   https://learn.microsoft.com/azure/foundry/agents/how-to/publish-copilot-virtual-network
3. What are hosted agents? (Responses/Invocations/Activity; Responses→Activity auto-bridge;
   dedicated Entra identity + endpoint) —
   https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents
4. Foundry Hosted Agents (agent-framework hosting) — "Microsoft Foundry Hosted Agents is generally
   available"; Python `agent-framework-foundry-hosting` integration is prerelease —
   https://learn.microsoft.com/agent-framework/hosting/foundry-hosted-agent
5. Configure and share your agent (agent object model: Responses/Activity/Invocations; **A2A
   (preview)**, **MCP (preview)**; auth schemes Entra / BotServiceRbac / BotServiceTenant; Foundry
   Agent Consumer role) — https://learn.microsoft.com/azure/foundry/agents/how-to/configure-agent
6. Microsoft Foundry provider (`FoundryAgent` service-managed sessions require `allow_preview=True`;
   preview `AIProjectClient` session API) —
   https://learn.microsoft.com/agent-framework/agents/providers/microsoft-foundry
7. Microsoft Foundry portal general availability overview (portal GA; GA-vs-Preview rollout
   pitfalls; private ACR only for projects created after 2026-06-25; Traces & Workflow Agents
   network-isolation gaps) — https://learn.microsoft.com/azure/foundry/concepts/general-availability
8. Custom engine agents for Microsoft 365 overview (two Foundry→M365 approaches: direct publish vs
   Agents Toolkit proxy; low-code vs pro-code; Copilot Studio managed SaaS) —
   https://learn.microsoft.com/microsoft-365/copilot/extensibility/overview-custom-engine-agent
9. Microsoft 365 Agents Toolkit (Teams Toolkit successor; Agents Playground; SSO, data storage,
   serverless, CI/CD for GitHub & Azure DevOps; multi-channel) —
   https://learn.microsoft.com/microsoftteams/platform/toolkit/overview-agents-toolkit
10. Build custom engine agents with Microsoft 365 Agents SDK (publishing via Agents Toolkit not
    supported in Microsoft 365 Government; JS/TS today, Python planned) —
    https://learn.microsoft.com/microsoft-365/copilot/extensibility/m365-agents-sdk
11. Get started with Copilot Studio for Teams (add Microsoft 365 and Microsoft Teams channel; org
    sharing requires admin approval) —
    https://learn.microsoft.com/microsoft-copilot-studio/fundamentals-get-started-teams
12. Hosted agent permissions reference (Azure Bot Service setup; publish permission
    troubleshooting) —
    https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agent-permissions
13. What is Microsoft Foundry Agent Service? (agent types; enterprise capabilities: agent identity,
    private networking, RBAC, content safety; publishing/versioning) —
    https://learn.microsoft.com/azure/foundry/agents/overview
14. Publish your agent as an Agent Application (Agent Application protocols; Responses vs Activity;
    publishing to M365/Teams) —
    https://learn.microsoft.com/azure/foundry/agents/how-to/agent-applications
15. Create and deploy an agent with Microsoft 365 Agents SDK (model-/orchestrator-agnostic;
    multi-channel incl. Teams and M365 Copilot) —
    https://learn.microsoft.com/microsoft-365/copilot/extensibility/create-deploy-agents-sdk
16. Understanding Activity Protocol (Bot Framework protocol used by Teams; Markdown text,
    attachments, citations handling) —
    https://learn.microsoft.com/microsoft-365/agents-sdk/activity-protocol
17. Enhance AI-generated agent messages — Citations (inline footnote citations render natively in
    the Teams client for AI-generated bot messages) —
    https://learn.microsoft.com/microsoftteams/platform/bots/how-to/bot-messages-ai-generated-content#citations
18. Enhance the Teams Experience (Teams SDK / Agents SDK: Adaptive Cards, clarification cards,
    suggested prompts, feedback controls, citations) —
    https://learn.microsoft.com/microsoftteams/platform/teams-sdk/in-depth-guides/ai-integrations/teams-enhancements
19. Agent identity concepts in Microsoft Foundry (attended OBO vs unattended app-only auth;
    dedicated Entra agent identity) —
    https://learn.microsoft.com/azure/foundry/agents/concepts/agent-identity
20. Authenticate users and acquire tokens for interactive agents (OBO exchange for downstream APIs;
    Microsoft.Identity.Web) —
    https://learn.microsoft.com/entra/agent-id/interactive-agent-authentication-authorization-flow
21. Isolate hosted agent sessions per user (`x-ms-user-identity` delegation; trusted service is the
    trust boundary; `UserIdentityImpersonation/action` permission) —
    https://learn.microsoft.com/azure/foundry/agents/how-to/isolate-sessions-per-user

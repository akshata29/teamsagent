// Workflow visualization data — two tabs toggle the Option A vs Option B subgraphs.
import type { WorkflowTab } from '@/components/workflow/workflowTypes'

const hostedAgentDetail = {
  title: 'Capital Markets Hosted Agent',
  subtitle: 'hosted agent · agent/app.py',
  description:
    'Foundry hosted-agent container (Agent Framework FoundryChatClient) that answers Capital Markets research questions grounded in Azure AI Search. Invoked via the Responses API.',
  sourceFiles: ['agent/app.py', 'agent/tools/search_tool.py', 'backend/app/services/foundry_service.py'],
  responsibilities: [
    'Run the Agent Framework tool loop',
    'Call the in-container Search tool (APP-ONLY)',
    'Synthesize a grounded, cited answer',
  ],
  dataFlow: [
    '1. Receives query (+ optional injected grounding) via Responses API',
    '2. Calls search_capital_markets_docs (app-only) for Option A',
    '3. Returns grounded Markdown answer',
  ],
  technologies: ['Microsoft Foundry hosted agent', 'Agent Framework', 'gpt-4o-class model'],
  keyFacts: [
    'Hosting gateway strips the Authorization header — the in-container tool cannot get the user token',
    'Per-user OBO therefore happens in the proxy/backend, not this container',
  ],
}

const aiSearchDetail = {
  title: 'Azure AI Search index',
  subtitle: 'datastore · capmarkets-research',
  description:
    'Vector + keyword index with permissionFilter ACL fields and a group_ids trimming field over synthetic Capital Markets research (information-barrier ACLs).',
  sourceFiles: ['deploy/create_index.py', 'deploy/seed_synthetic_data.py'],
  responsibilities: ['Vector + keyword retrieval', 'Native ACL / security trimming'],
  dataFlow: [
    '1. Receives query (+ optional user token)',
    '2. Trims per ACL (x-ms-query-source-authorization) or app-only filter',
    '3. Returns entitled hits',
  ],
  technologies: ['Azure AI Search', 'HNSW vectors', 'permissionFilter (2026-05-01-preview)'],
}

export const workflowTabs: WorkflowTab[] = [
  {
    id: 'option-a',
    label: 'Option A · Direct Publish',
    description:
      'Direct Foundry publish to Teams / M365 Copilot via Azure Bot Service. The in-container Search tool runs app-only — the Teams user token never reaches it, so results are an undifferentiated slice.',
    nodes: [
      {
        id: 'bot-service',
        type: 'service',
        label: 'Teams / M365 Copilot',
        subtitle: 'Azure Bot Service',
        position: { x: 320, y: 20 },
        detail: {
          title: 'Option A — Direct publish (Azure Bot Service)',
          subtitle: 'outcome · deploy/publish_teams_optionA.py',
          description:
            'Azure Bot Service bridges Teams / M365 Copilot to the agent activity endpoint. App-only channel auth (BotServiceTenant) — no per-user OBO.',
          sourceFiles: ['deploy/publish_teams_optionA.py', 'deploy/bicep/botservice.bicep'],
          responsibilities: [
            'Enable activity protocol + BotServiceTenant auth scheme',
            'Create Bot Service + MsTeams channel',
            'Emit + submit the Teams app manifest',
          ],
          dataFlow: [
            '1. Teams message → Bot Service',
            '2. Responses→Activity bridge → agent',
            '3. Text reply back to Teams',
          ],
          technologies: ['Azure Bot Service', 'Activity protocol 2025-05-15-preview'],
          keyFacts: ['Isolation key source = N/A → no per-user token flows through'],
        },
      },
      {
        id: 'hosted-agent-a',
        type: 'agent',
        label: 'Capital Markets Hosted Agent',
        subtitle: 'agent · app.py',
        position: { x: 320, y: 160 },
        detail: hostedAgentDetail,
      },
      {
        id: 'search-tool',
        type: 'service',
        label: 'search_capital_markets_docs',
        subtitle: 'in-container tool',
        position: { x: 320, y: 300 },
        detail: {
          title: 'In-container Search tool (app-only)',
          subtitle: 'tool · agent/tools/search_tool.py',
          description:
            'App-only vector query. Cannot receive the end-user token (gateway strips Authorization) — used by Option A only.',
          sourceFiles: ['agent/tools/search_tool.py'],
          responsibilities: ['Vector + keyword query', 'App-identity scope only (excludes MNPI)'],
          dataFlow: ['1. Receives query', '2. Queries AI Search with project MI', '3. Returns app-scoped hits'],
          technologies: ['azure-search-documents 12.1.0b1', 'Project managed identity'],
        },
      },
      {
        id: 'ai-search-a',
        type: 'datastore',
        label: 'Azure AI Search',
        subtitle: 'capmarkets-research',
        position: { x: 320, y: 440 },
        detail: aiSearchDetail,
      },
    ],
    edges: [
      { id: 'a1', source: 'bot-service', target: 'hosted-agent-a', label: 'activity bridge' },
      { id: 'a2', source: 'hosted-agent-a', target: 'search-tool', label: 'tool call' },
      { id: 'a3', source: 'search-tool', target: 'ai-search-a', label: 'app-only query' },
    ],
  },
  {
    id: 'option-b',
    label: 'Option B · Agents SDK Proxy',
    description:
      'M365 Agents SDK Custom Engine Agent proxy is the trust boundary: Teams SSO → OBO → per-user AI Search trimming → grounding injected into the hosted agent. Real document-level security.',
    nodes: [
      {
        id: 'agents-proxy',
        type: 'service',
        label: 'Agents SDK Proxy',
        subtitle: 'Custom Engine Agent',
        position: { x: 320, y: 20 },
        detail: {
          title: 'Option B — M365 Agents SDK proxy',
          subtitle: 'service · proxy/',
          description:
            'Custom Engine Agent doing Teams SSO → MSAL OBO → per-user AI Search → calls the hosted agent. The trust boundary for per-user OBO.',
          sourceFiles: ['proxy/src/', 'backend/app/routers/demo.py'],
          responsibilities: ['Teams SSO + OBO exchange', 'Per-user retrieval', 'Invoke hosted agent'],
          dataFlow: [
            '1. Teams SSO → user token',
            '2. OBO → search-scoped token',
            '3. Trimmed retrieval → grounding → agent',
          ],
          technologies: ['M365 Agents Toolkit', 'M365 Agents SDK', 'MSAL OBO'],
        },
      },
      {
        id: 'obo-retrieval',
        type: 'service',
        label: 'Per-user OBO Retrieval',
        subtitle: 'obo + search_obo',
        position: { x: 320, y: 160 },
        detail: {
          title: 'Per-user OBO Retrieval (Option B)',
          subtitle: 'service · backend/app/services/obo_service.py + search_service.py',
          description:
            'Exchanges the Teams-user token (OBO) and queries AI Search with x-ms-query-source-authorization for per-user document trimming (native ACL, preview).',
          sourceFiles: [
            'backend/app/services/obo_service.py',
            'backend/app/services/search_service.py',
            'backend/app/services/retrieval_service.py',
          ],
          responsibilities: [
            'OBO exchange to search scope',
            'Native-ACL trimmed retrieval',
            'Inject trimmed docs into the agent as grounding',
          ],
          dataFlow: [
            '1. Receives user assertion + query',
            '2. OBO → search token',
            '3. Query w/ x-ms-query-source-authorization',
            '4. Inject grounding into agent',
          ],
          technologies: ['azure-identity OnBehalfOfCredential', 'AI Search 2026-05-01-preview ACLs'],
          keyFacts: ['Fail-closed: no user token ⇒ public-only documents'],
        },
      },
      {
        id: 'ai-search-b',
        type: 'datastore',
        label: 'Azure AI Search',
        subtitle: 'capmarkets-research',
        position: { x: 140, y: 320 },
        detail: aiSearchDetail,
      },
      {
        id: 'hosted-agent-b',
        type: 'agent',
        label: 'Capital Markets Hosted Agent',
        subtitle: 'agent · app.py',
        position: { x: 500, y: 320 },
        detail: hostedAgentDetail,
      },
    ],
    edges: [
      { id: 'b1', source: 'agents-proxy', target: 'obo-retrieval', label: 'SSO → OBO' },
      { id: 'b2', source: 'obo-retrieval', target: 'ai-search-b', label: 'x-ms-query-source-authorization' },
      { id: 'b3', source: 'obo-retrieval', target: 'hosted-agent-b', label: 'grounding + Responses API' },
    ],
  },
]

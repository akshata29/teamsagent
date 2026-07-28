import { ShieldCheck, Server, Search, KeyRound, Bot, Cpu } from 'lucide-react'
import PageHeader from '@/components/PageHeader'

interface ServiceCard {
  icon: typeof Server
  name: string
  status: 'GA' | 'Preview'
  description: string
}

const SERVICES: ServiceCard[] = [
  {
    icon: Bot,
    name: 'Microsoft Foundry — Hosted Agent',
    status: 'GA',
    description:
      'Container-hosted Capital Markets research agent (Agent Framework), invoked via the Responses API with agent_reference.',
  },
  {
    icon: Search,
    name: 'Azure AI Search — Document-level security',
    status: 'Preview',
    description:
      'Native ACL trimming (permissionFilter + x-ms-query-source-authorization, 2026-05-01-preview) with a GA security-trimming fallback.',
  },
  {
    icon: KeyRound,
    name: 'Entra ID — On-Behalf-Of',
    status: 'GA',
    description:
      'OnBehalfOfCredential exchanges the Teams-user token for a Search-scoped token (https://search.azure.com/.default).',
  },
  {
    icon: Server,
    name: 'Azure Bot Service — Option A',
    status: 'GA',
    description:
      'Direct Foundry publish to Teams / M365 Copilot via the Activity protocol. App-only channel auth.',
  },
  {
    icon: Cpu,
    name: 'M365 Agents Toolkit / SDK — Option B',
    status: 'GA',
    description:
      'Custom Engine Agent proxy: Teams SSO → OBO → per-user retrieval → hosted agent. The trust boundary.',
  },
]

export default function ArchitecturePage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Architecture"
        subtitle="Azure services behind the Option A vs Option B Capital Markets Teams agent."
      />

      <div className="rounded-xl border border-accent/40 bg-accent/5 p-5 flex items-start gap-3">
        <ShieldCheck size={20} className="text-accent-hover mt-0.5 shrink-0" />
        <div>
          <div className="text-sm font-semibold text-gray-100">
            The OBO trust boundary lives in the proxy/backend — not the hosted agent tool
          </div>
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">
            The Foundry hosting gateway strips the Authorization header before requests reach the
            container, so the in-container Search tool cannot obtain the end-user token. Per-user
            document-level trimming is therefore performed at the trust boundary (the Agents SDK
            proxy / backend), which does the OBO exchange and queries AI Search with
            <span className="font-mono text-gray-300"> x-ms-query-source-authorization</span>. This
            is why Option A is app-only and Option B is per-user.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {SERVICES.map((s) => (
          <div key={s.name} className="card p-5">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <s.icon size={18} className="text-accent-hover" />
                <span className="text-sm font-semibold text-gray-100">{s.name}</span>
              </div>
              <span className={s.status === 'GA' ? 'badge badge-success' : 'badge badge-warning'}>
                {s.status}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-3 leading-relaxed">{s.description}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'
import { demoApi } from '@/api/client'
import PageHeader from '@/components/PageHeader'

function Flag({ label, on, hint }: { label: string; on: boolean; hint: string }) {
  return (
    <div className="flex items-center justify-between px-3 py-2.5 rounded-lg bg-surface-50">
      <div>
        <div className="text-sm text-gray-200">{label}</div>
        <div className="text-[11px] text-gray-500">{hint}</div>
      </div>
      <span className={clsx('badge', on ? 'badge-success' : 'badge-warning')}>
        {on ? 'ON' : 'OFF'}
      </span>
    </div>
  )
}

export default function SettingsPage() {
  const { data } = useQuery({ queryKey: ['settings'], queryFn: demoApi.getSettings })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="Effective backend configuration (secrets are never exposed)."
      />

      {data && (
        <>
          <div className="card p-5 space-y-2">
            <div className="section-title mb-2">Feature flags</div>
            <Flag
              label="Native AI Search ACL"
              on={data.use_native_acl}
              hint="x-ms-query-source-authorization (2026-05-01-preview) vs GA security trimming"
            />
            <Flag
              label="Use deployed Foundry agent"
              on={data.use_deployed_agent}
              hint="Invoke the deployed hosted agent via the Responses API"
            />
            <Flag
              label="Offline demo mode"
              on={data.offline_mode}
              hint="Run the full demo with synthetic data and no Azure calls"
            />
            <Flag
              label="Azure configured"
              on={data.azure_configured}
              hint="Core Foundry + Search endpoints are present"
            />
          </div>

          <div className="card p-5">
            <div className="section-title mb-3">Effective values</div>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-gray-500">Search API version</dt>
              <dd className="text-gray-200 font-mono">{data.search_api_version}</dd>
              <dt className="text-gray-500">Foundry agent name</dt>
              <dd className="text-gray-200 font-mono">{data.foundry_agent_name}</dd>
              <dt className="text-gray-500">Default Option B variant</dt>
              <dd className="text-gray-200 font-mono">{data.default_b_variant}</dd>
            </dl>
          </div>
        </>
      )}
    </div>
  )
}

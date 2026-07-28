import { AlertTriangle } from 'lucide-react'
import type { CompareResult } from '@/types/demo'
import OptionPane from './OptionPane'

interface Props {
  compare?: CompareResult
  loading?: boolean
}

export default function CompareView({ compare, loading }: Props) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <OptionPane
          title="Option A · Direct Foundry publish"
          subtitle="Hosted agent · app/admin identity (no per-user OBO)"
          result={compare?.option_a}
          loading={loading}
          accent="a"
        />
        <OptionPane
          title="Option B · M365 Agents SDK proxy"
          subtitle="Teams SSO → OBO → per-user document trimming"
          result={compare?.option_b}
          loading={loading}
          accent="b"
        />
      </div>

      {compare && compare.difference_doc_ids.length > 0 && (
        <div className="rounded-xl border border-status-warning/40 bg-status-warning/5 p-4 flex items-start gap-3">
          <AlertTriangle size={18} className="text-status-warning mt-0.5 shrink-0" />
          <div>
            <div className="text-sm font-semibold text-gray-100">
              Option A over-shared {compare.difference_doc_ids.length} document
              {compare.difference_doc_ids.length > 1 ? 's' : ''}
            </div>
            <div className="text-xs text-gray-400 mt-1">
              These documents were returned by Option A (app-only) but correctly trimmed by
              Option B's per-user OBO for this persona:{' '}
              <span className="font-mono text-gray-300">
                {compare.difference_doc_ids.join(', ')}
              </span>
            </div>
          </div>
        </div>
      )}

      {compare && compare.difference_doc_ids.length === 0 && (
        <div className="rounded-xl border border-border bg-card p-4 text-xs text-gray-400">
          No difference for this persona/query — both paths returned the same documents.
        </div>
      )}
    </div>
  )
}

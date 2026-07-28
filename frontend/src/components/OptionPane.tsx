import clsx from 'clsx'
import { ShieldCheck, ShieldAlert, Lock } from 'lucide-react'
import type { DocHit, IdentityBasis, InvokeResult } from '@/types/demo'

const BASIS_META: Record<IdentityBasis, { label: string; cls: string; Icon: typeof Lock }> = {
  app_only: { label: 'App-only identity', cls: 'badge-warning', Icon: ShieldAlert },
  per_user_obo: { label: 'Per-user OBO', cls: 'badge-success', Icon: ShieldCheck },
  public_only: { label: 'Public-only (fail-closed)', cls: 'badge-error', Icon: Lock },
}

const CLS_BADGE: Record<string, string> = {
  public: 'badge-info',
  internal: 'badge-accent',
  mnpi: 'badge-error',
}

function DocRow({ doc }: { doc: DocHit }) {
  return (
    <div className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-surface-50">
      <div className="min-w-0">
        <div className="text-xs font-medium text-gray-200 truncate">{doc.title}</div>
        <div className="text-[10px] text-gray-500 font-mono">{doc.id}</div>
      </div>
      <span className={clsx('badge', CLS_BADGE[doc.classification])}>{doc.classification}</span>
    </div>
  )
}

interface Props {
  title: string
  subtitle: string
  result?: InvokeResult
  loading?: boolean
  accent?: 'a' | 'b'
}

export default function OptionPane({ title, subtitle, result, loading, accent = 'a' }: Props) {
  const basis = result ? BASIS_META[result.identity_basis] : null
  return (
    <div className="card p-5 flex flex-col gap-4 h-full">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={clsx(
                'w-2 h-2 rounded-full',
                accent === 'a' ? 'bg-status-warning' : 'bg-status-success',
              )}
            />
            <h3 className="text-sm font-bold text-gray-100">{title}</h3>
          </div>
          <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>
        </div>
        {basis && (
          <span className={clsx('badge inline-flex items-center gap-1', basis.cls)}>
            <basis.Icon size={11} />
            {basis.label}
          </span>
        )}
      </div>

      {loading && <div className="text-xs text-gray-500 animate-pulse">Running…</div>}

      {result && !loading && (
        <>
          <div className="rounded-lg bg-surface-50 p-3 text-xs text-gray-200 leading-relaxed whitespace-pre-wrap">
            {result.answer}
          </div>
          {result.note && (
            <p className="text-[11px] text-gray-500 italic leading-snug">{result.note}</p>
          )}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <span className="stat-label">Documents returned ({result.doc_hits.length})</span>
              <span className="text-[10px] text-gray-600">{result.latency_ms} ms</span>
            </div>
            <div className="space-y-1.5">
              {result.doc_hits.map((d) => (
                <DocRow key={d.id} doc={d} />
              ))}
              {result.doc_hits.length === 0 && (
                <div className="text-xs text-gray-500">No entitled documents.</div>
              )}
            </div>
          </div>
        </>
      )}

      {!result && !loading && (
        <div className="text-xs text-gray-600">Run a query to see results.</div>
      )}
    </div>
  )
}

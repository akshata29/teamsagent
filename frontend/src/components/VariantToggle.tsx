import clsx from 'clsx'

interface Props {
  value: 'b1' | 'b2'
  onChange: (v: 'b1' | 'b2') => void
}

const OPTIONS: { id: 'b1' | 'b2'; label: string; hint: string }[] = [
  { id: 'b1', label: 'B1 · Proxy retrieve', hint: 'Proxy OBO → AI Search → grounding (GA path)' },
  { id: 'b2', label: 'B2 · Inline MCP', hint: 'Per-request token in the model run (preview)' },
]

export default function VariantToggle({ value, onChange }: Props) {
  return (
    <div className="inline-flex rounded-lg border border-border bg-card p-0.5">
      {OPTIONS.map((o) => (
        <button
          key={o.id}
          title={o.hint}
          onClick={() => onChange(o.id)}
          className={clsx(
            'px-3 py-1.5 text-xs font-medium rounded-md transition-colors',
            value === o.id ? 'bg-accent/20 text-accent-hover' : 'text-gray-400 hover:text-gray-200',
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

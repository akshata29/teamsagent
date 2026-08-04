import clsx from 'clsx'
import { UserCircle } from 'lucide-react'
import type { Persona } from '@/types/demo'

interface Props {
  personas: Persona[]
  selectedId: string
  onSelect: (id: string) => void
}

export default function PersonaPicker({ personas, selectedId, onSelect }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      {personas.map((p) => {
        const active = p.id === selectedId
        return (
          <button
            key={p.id}
            onClick={() => onSelect(p.id)}
            className={clsx(
              'text-left rounded-xl border p-4 transition-colors',
              active
                ? 'border-accent bg-accent/10'
                : 'border-border bg-card hover:bg-surface-50',
            )}
          >
            <div className="flex items-center gap-2">
              <UserCircle size={18} className={active ? 'text-accent-hover' : 'text-gray-500'} />
              <span className="text-sm font-semibold text-gray-100">{p.display_name}</span>
            </div>
            <div className="text-xs text-gray-400 mt-1">{p.role}</div>
            <div className="text-[11px] text-gray-500 mt-2 leading-snug">{p.entitlement_summary}</div>
            <div className="text-[10px] text-gray-600 mt-2 font-mono truncate">
              user: {p.entra_group_id}
            </div>
          </button>
        )
      })}
    </div>
  )
}

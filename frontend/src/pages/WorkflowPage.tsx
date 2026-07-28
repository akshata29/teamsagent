import { useState } from 'react'
import { GitBranch } from 'lucide-react'
import WorkflowDiagram from '@/components/workflow/WorkflowDiagram'
import { workflowTabs } from '@/data/workflowData'
import type { NodeType } from '@/components/workflow/workflowTypes'

const LEGEND: { type: NodeType; label: string; dotClass: string }[] = [
  { type: 'service', label: 'Service / API', dotClass: 'bg-blue-500' },
  { type: 'agent', label: 'Foundry AI Agent', dotClass: 'bg-indigo-500' },
  { type: 'gate', label: 'Human Gate', dotClass: 'bg-amber-500' },
  { type: 'datastore', label: 'Data Store', dotClass: 'bg-teal-500' },
  { type: 'outcome', label: 'Outcome', dotClass: 'bg-green-500' },
]

export default function WorkflowPage() {
  const [activeTabId, setActiveTabId] = useState<string>(workflowTabs[0].id)
  const activeTab = workflowTabs.find((t) => t.id === activeTabId) ?? workflowTabs[0]

  return (
    <div className="flex flex-col h-full -m-6 overflow-hidden">
      <div className="flex-shrink-0 px-6 py-4 bg-surface-100 border-b border-border">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-accent" />
              <h1 className="text-base font-bold text-gray-100">Teams Integration Workflow</h1>
            </div>
            <p className="text-gray-500 text-xs mt-0.5">
              Toggle Option A vs Option B — click any component for details
            </p>
          </div>
          <div className="hidden md:flex items-center gap-4 flex-wrap">
            {LEGEND.map((item) => (
              <div key={item.type} className="flex items-center gap-1.5">
                <div className={`w-2.5 h-2.5 rounded-sm flex-shrink-0 ${item.dotClass}`} />
                <span className="text-gray-400 text-xs">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
        <p className="text-gray-400 text-xs mt-2 max-w-3xl">{activeTab.description}</p>
      </div>

      <div className="flex-shrink-0 px-6 bg-surface-100/60 border-b border-border">
        <nav className="flex gap-0.5 -mb-px" aria-label="Workflow tabs">
          {workflowTabs.map((tab) => {
            const isActive = tab.id === activeTabId
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTabId(tab.id)}
                className={[
                  'px-4 py-2.5 text-sm font-medium rounded-t-md border-b-2 transition-colors whitespace-nowrap',
                  isActive
                    ? 'border-accent text-accent-hover bg-accent/10'
                    : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-surface-50',
                ].join(' ')}
                aria-current={isActive ? 'page' : undefined}
              >
                {tab.label}
              </button>
            )
          })}
        </nav>
      </div>

      <div className="flex-1 overflow-hidden flex">
        <WorkflowDiagram tab={activeTab} />
      </div>
    </div>
  )
}

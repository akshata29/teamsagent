import { useEffect, useRef, useState } from 'react'
import { useMsal } from '@azure/msal-react'
import type { AccountInfo } from '@azure/msal-browser'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Play, Sparkles } from 'lucide-react'
import { demoApi } from '@/api/client'
import type { CompareResult, Persona } from '@/types/demo'
import PageHeader from '@/components/PageHeader'
import PersonaPicker from '@/components/PersonaPicker'
import VariantToggle from '@/components/VariantToggle'
import CompareView from '@/components/CompareView'
import DocTrimVisualizer from '@/components/DocTrimVisualizer'

const SAMPLE_QUERIES = [
  'What is our semiconductor sector view?',
  'Any high-yield energy credit ideas?',
  'Summarize the Project Falcon deal memo',
  'What is our duration positioning?',
]

const norm = (s?: string | null) => (s ?? '').toLowerCase().replace(/[^a-z0-9]/g, '')

/** Match the signed-in Entra account to a persona by display name / UPN (best-effort). */
function matchPersona(personas: Persona[], account?: AccountInfo | null): Persona | undefined {
  if (!account) return undefined
  const name = norm(account.name)
  const user = norm(account.username)
  return personas.find((p) => {
    const disp = norm(p.display_name)
    return disp.length > 2 && (name.includes(disp) || user.includes(disp))
  })
}

export default function DemoPage() {
  const { accounts } = useMsal()
  const account = accounts[0] ?? null

  const [personaId, setPersonaId] = useState('equity-research')
  const [query, setQuery] = useState(SAMPLE_QUERIES[0])
  const [variant, setVariant] = useState<'b1' | 'b2'>('b1')
  const [compare, setCompare] = useState<CompareResult | undefined>()

  const personasQ = useQuery({ queryKey: ['personas'], queryFn: demoApi.getPersonas })
  const corpusQ = useQuery({ queryKey: ['corpus'], queryFn: demoApi.getCorpus })

  // Auto-select the persona that matches the actual signed-in user (once).
  const autoSelected = useRef(false)
  const signedInPersona = matchPersona(personasQ.data ?? [], account)
  useEffect(() => {
    if (!autoSelected.current && signedInPersona) {
      setPersonaId(signedInPersona.id)
      autoSelected.current = true
    }
  }, [signedInPersona])

  const runM = useMutation({
    mutationFn: () => demoApi.compare({ persona_id: personaId, query, variant }),
    onSuccess: setCompare,
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Capital Markets Agent — Teams Integration Demo"
        subtitle="Compare Option A (direct Foundry publish) vs Option B (Agents SDK proxy) with per-user document-level security via OBO."
      />

      <div className="card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="section-title">1 · Choose a user (information barrier)</div>
          {signedInPersona && (
            <span className="text-[11px] text-status-success">
              Signed in as {signedInPersona.display_name} · {signedInPersona.role}
            </span>
          )}
        </div>
        {personasQ.data && (
          <PersonaPicker
            personas={personasQ.data}
            selectedId={personaId}
            onSelect={setPersonaId}
          />
        )}
      </div>

      <div className="card p-5 space-y-3">
        <div className="flex items-center justify-between">
          <div className="section-title">2 · Ask the research desk</div>
          <VariantToggle value={variant} onChange={setVariant} />
        </div>
        <div className="flex gap-2">
          <input
            className="input flex-1"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a Capital Markets research question…"
          />
          <button
            className="btn-primary inline-flex items-center gap-2"
            onClick={() => runM.mutate()}
            disabled={runM.isPending || !query.trim()}
          >
            <Play size={14} />
            Run both options
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => setQuery(q)}
              className="text-[11px] px-2.5 py-1 rounded-full border border-border text-gray-400 hover:text-gray-100 hover:bg-surface-50 inline-flex items-center gap-1"
            >
              <Sparkles size={10} /> {q}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <div className="section-title">3 · Side-by-side result</div>
        <CompareView compare={compare} loading={runM.isPending} />
      </div>

      {corpusQ.data && (
        <DocTrimVisualizer
          corpus={corpusQ.data}
          compare={compare}
          currentUserLabel={signedInPersona?.display_name}
        />
      )}
    </div>
  )
}

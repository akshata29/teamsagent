import clsx from 'clsx'
import type { CompareResult, DocHit } from '@/types/demo'

interface Props {
  corpus: DocHit[]
  compare?: CompareResult
}

type Cell = 'visible' | 'trimmed'

function cellClass(state: Cell) {
  return state === 'visible'
    ? 'bg-status-success/20 text-status-success border-status-success/30'
    : 'bg-surface-50 text-gray-600 border-border'
}

/**
 * Grid showing, for each document, whether Option A and Option B expose it to the
 * selected persona. The A/B delta is the document-level-security teaching point.
 */
export default function DocTrimVisualizer({ corpus, compare }: Props) {
  const aVisible = new Set(compare?.option_a.visible_doc_ids ?? [])
  const bVisible = new Set(compare?.option_b.visible_doc_ids ?? [])
  const diff = new Set(compare?.difference_doc_ids ?? [])

  return (
    <div className="card p-5">
      <div className="section-title mb-1">Document-level access map</div>
      <p className="text-xs text-gray-500 mb-4">
        Green = returned to the selected persona. Rows highlighted amber are documents Option A
        exposed that Option B correctly trimmed away.
      </p>
      <div className="space-y-1.5">
        <div className="grid grid-cols-12 gap-2 text-[10px] uppercase tracking-wider text-gray-600 px-1">
          <div className="col-span-8">Document</div>
          <div className="col-span-2 text-center">Option A</div>
          <div className="col-span-2 text-center">Option B</div>
        </div>
        {corpus.map((doc) => {
          const isDiff = diff.has(doc.id)
          return (
            <div
              key={doc.id}
              className={clsx(
                'grid grid-cols-12 gap-2 items-center rounded-lg px-2 py-2 border',
                isDiff ? 'border-status-warning/50 bg-status-warning/5' : 'border-transparent',
              )}
            >
              <div className="col-span-8 min-w-0">
                <div className="text-xs text-gray-200 truncate">{doc.title}</div>
                <div className="text-[10px] font-mono text-gray-600">
                  {doc.id} · {doc.classification}
                </div>
              </div>
              <div className="col-span-2 flex justify-center">
                <span
                  className={clsx(
                    'text-[10px] px-2 py-0.5 rounded border',
                    cellClass(aVisible.has(doc.id) ? 'visible' : 'trimmed'),
                  )}
                >
                  {aVisible.has(doc.id) ? 'shown' : 'hidden'}
                </span>
              </div>
              <div className="col-span-2 flex justify-center">
                <span
                  className={clsx(
                    'text-[10px] px-2 py-0.5 rounded border',
                    cellClass(bVisible.has(doc.id) ? 'visible' : 'trimmed'),
                  )}
                >
                  {bVisible.has(doc.id) ? 'shown' : 'hidden'}
                </span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

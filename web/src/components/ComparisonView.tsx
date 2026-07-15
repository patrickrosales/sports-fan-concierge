import { PlanCard } from './PlanCard'
import { renderBold } from '../lib/markdown'
import type { ComparisonResult } from '../lib/stream'

interface Props {
  comparison: ComparisonResult
}

export function ComparisonView({ comparison }: Props) {
  const { options, recommendation } = comparison

  return (
    <div className="w-full max-w-5xl mx-auto space-y-6">
      <div
        className={`grid gap-4 ${options.length > 1 ? 'md:grid-cols-2' : ''}`}
      >
        {options.map((option) => (
          <div key={option.label} className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-linear-text-quaternary px-1">
              {option.label}
            </p>
            <PlanCard plan={option.plan} bare />
          </div>
        ))}
      </div>

      <div className="w-full max-w-2xl mx-auto rounded-lg border border-accent-700/40 bg-accent-800/60 px-4 py-3">
        <p className="text-xs font-medium uppercase tracking-wide text-accent-400">
          Concierge recommendation
        </p>
        <p className="mt-1 text-sm text-linear-text-secondary">{renderBold(recommendation)}</p>
      </div>
    </div>
  )
}

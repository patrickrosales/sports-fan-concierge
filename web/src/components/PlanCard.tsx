import type { GameNightPlan } from '../lib/stream'
import { renderBold } from '../lib/markdown'

interface Props {
  plan: GameNightPlan
  /** Set by ComparisonView so cards fill a grid cell instead of centering themselves. */
  bare?: boolean
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 text-xs font-medium uppercase tracking-wide text-linear-text-quaternary">
      {children}
    </p>
  )
}

export function PlanCard({ plan, bare = false }: Props) {
  const { game, seating, dining, getting_there, summary } = plan
  const wrapper = bare ? 'w-full' : 'w-full max-w-2xl mx-auto'

  if (!game) {
    return (
      <div className={`${wrapper} rounded-lg border border-linear-border bg-linear-surface/60 p-6`}>
        <p className="text-xs font-medium uppercase tracking-wide text-linear-text-quaternary">
          No matching game
        </p>
        <p className="mt-2 text-sm text-linear-text-secondary">{renderBold(summary)}</p>
      </div>
    )
  }

  return (
    <div className={`${wrapper} rounded-lg border border-linear-border bg-linear-surface/60 p-6`}>
      <div className="border-b border-linear-border pb-4">
        <p className="text-xs font-medium uppercase tracking-wide text-accent-400">
          {game.league}
        </p>
        <h2 className="mt-1 text-lg font-semibold text-linear-text">
          {game.team} vs {game.opponent}
        </h2>
        <p className="mt-1 text-sm text-linear-text-tertiary">
          {game.date} · {game.time} · {game.venue}
        </p>
        <p className="mt-2 text-sm text-linear-text-secondary">{game.why}</p>
      </div>

      {seating.length > 0 && (
        <div className="border-b border-linear-border py-4">
          <SectionLabel>Seating</SectionLabel>
          <div className="space-y-2">
            {seating.map((s) => (
              <div key={s.tier} className="flex items-baseline justify-between gap-4 text-sm">
                <div className="min-w-0">
                  <span className="font-medium text-linear-text">{s.tier}</span>
                  <span className="ml-2 text-linear-text-tertiary">{s.vibe}</span>
                </div>
                <span className="shrink-0 text-linear-text-tertiary">{s.price_range}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {dining.length > 0 && (
        <div className="border-b border-linear-border py-4">
          <SectionLabel>Dining</SectionLabel>
          <ul className="space-y-1.5 text-sm">
            {dining.map((d) => (
              <li key={d.name}>
                <span className="font-medium text-linear-text">{d.name}</span>
                <span className="text-linear-text-tertiary"> — {d.detail}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {getting_there.length > 0 && (
        <div className="py-4">
          <SectionLabel>Getting there</SectionLabel>
          <ul className="space-y-1.5 text-sm">
            {getting_there.map((t) => (
              <li key={t.name}>
                <span className="font-medium text-linear-text">{t.name}</span>
                <span className="text-linear-text-tertiary"> — {t.detail}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-4 border-t border-linear-border pt-4 text-sm text-linear-text-secondary">
        {renderBold(summary)}
      </p>
    </div>
  )
}

import type { GameNightPlan } from '../lib/stream'

interface Props {
  plan: GameNightPlan
  /** Set by ComparisonView so cards fill a grid cell instead of centering themselves. */
  bare?: boolean
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-2 text-xs font-medium uppercase tracking-wide text-neutral-400">
      {children}
    </p>
  )
}

export function PlanCard({ plan, bare = false }: Props) {
  const { game, seating, dining, getting_there, summary } = plan
  const wrapper = bare ? 'w-full' : 'w-full max-w-2xl mx-auto'

  if (!game) {
    return (
      <div
        className={`${wrapper} rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6`}
      >
        <p className="text-xs font-medium uppercase tracking-wide text-neutral-400">
          No matching game
        </p>
        <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-300">{summary}</p>
      </div>
    )
  }

  return (
    <div
      className={`${wrapper} rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-6`}
    >
      <div className="border-b border-neutral-100 dark:border-neutral-800 pb-4">
        <p className="text-xs font-medium uppercase tracking-wide text-indigo-500">
          {game.league}
        </p>
        <h2 className="mt-1 text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          {game.team} vs {game.opponent}
        </h2>
        <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
          {game.date} · {game.time} · {game.venue}
        </p>
        <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-300">{game.why}</p>
      </div>

      {seating.length > 0 && (
        <div className="border-b border-neutral-100 dark:border-neutral-800 py-4">
          <SectionLabel>Seating</SectionLabel>
          <div className="space-y-2">
            {seating.map((s) => (
              <div key={s.tier} className="flex items-baseline justify-between gap-4 text-sm">
                <div className="min-w-0">
                  <span className="font-medium text-neutral-900 dark:text-neutral-100">
                    {s.tier}
                  </span>
                  <span className="ml-2 text-neutral-500 dark:text-neutral-400">{s.vibe}</span>
                </div>
                <span className="shrink-0 text-neutral-500 dark:text-neutral-400">
                  {s.price_range}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {dining.length > 0 && (
        <div className="border-b border-neutral-100 dark:border-neutral-800 py-4">
          <SectionLabel>Dining</SectionLabel>
          <ul className="space-y-1.5 text-sm">
            {dining.map((d) => (
              <li key={d.name}>
                <span className="font-medium text-neutral-900 dark:text-neutral-100">
                  {d.name}
                </span>
                <span className="text-neutral-500 dark:text-neutral-400"> — {d.detail}</span>
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
                <span className="font-medium text-neutral-900 dark:text-neutral-100">
                  {t.name}
                </span>
                <span className="text-neutral-500 dark:text-neutral-400"> — {t.detail}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="mt-4 border-t border-neutral-100 dark:border-neutral-800 pt-4 text-sm text-neutral-600 dark:text-neutral-300">
        {summary}
      </p>
    </div>
  )
}

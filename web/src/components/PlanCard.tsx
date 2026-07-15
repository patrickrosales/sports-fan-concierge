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

const LINK_CLASS = 'text-accent-400 underline-offset-2 hover:text-accent-300 hover:underline'

export function PlanCard({ plan, bare = false }: Props) {
  const { game, venue_url, ticket_url, seating, dining, getting_there, summary } = plan
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
        <div className="mt-1 flex items-start justify-between gap-3">
          <h2 className="text-lg font-semibold text-linear-text">
            {game.team} vs {game.opponent}
          </h2>
          {ticket_url && (
            <a
              href={ticket_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`shrink-0 rounded-md border border-linear-border px-2.5 py-1 text-xs font-medium ${LINK_CLASS}`}
            >
              Get tickets
            </a>
          )}
        </div>
        <p className="mt-1 text-sm text-linear-text-tertiary">
          {game.date} · {game.time} ·{' '}
          {venue_url ? (
            <a href={venue_url} target="_blank" rel="noopener noreferrer" className={LINK_CLASS}>
              {game.venue}
            </a>
          ) : (
            game.venue
          )}
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
                {d.url ? (
                  <a href={d.url} target="_blank" rel="noopener noreferrer" className={`font-medium ${LINK_CLASS}`}>
                    {d.name}
                  </a>
                ) : (
                  <span className="font-medium text-linear-text">{d.name}</span>
                )}
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

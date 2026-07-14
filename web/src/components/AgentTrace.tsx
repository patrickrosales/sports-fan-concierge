const AGENT_LABELS: Record<string, string> = {
  find_games: 'Schedule Agent',
  recommend_seating: 'Venue Agent',
  local_experience: 'Local Experience Agent',
}

export interface TraceStep {
  agent: string
  status: 'running' | 'done'
  summary?: string
}

interface Props {
  steps: TraceStep[]
}

function Spinner() {
  return (
    <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-neutral-300 border-t-indigo-500 dark:border-neutral-700 dark:border-t-indigo-400" />
  )
}

function Check() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-3.5 w-3.5 text-emerald-500">
      <path
        fillRule="evenodd"
        d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
        clipRule="evenodd"
      />
    </svg>
  )
}

export function AgentTrace({ steps }: Props) {
  if (steps.length === 0) return null

  return (
    <div className="w-full max-w-2xl mx-auto rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 p-4">
      <p className="mb-3 text-xs font-medium uppercase tracking-wide text-neutral-400">
        Concierge team
      </p>
      <ul className="space-y-3">
        {steps.map((step, i) => (
          <li key={`${step.agent}-${i}`} className="flex items-start gap-3">
            <span className="mt-0.5 flex h-3.5 w-3.5 items-center justify-center">
              {step.status === 'running' ? <Spinner /> : <Check />}
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                {AGENT_LABELS[step.agent] ?? step.agent}
              </p>
              {step.summary && (
                <p className="mt-0.5 text-xs text-neutral-500 dark:text-neutral-400">
                  {step.summary}
                </p>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

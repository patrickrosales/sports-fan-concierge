import { useState } from 'react'
import { RequestBar } from './components/RequestBar'
import { AgentTrace, type TraceStep } from './components/AgentTrace'
import { PlanCard } from './components/PlanCard'
import { ComparisonView } from './components/ComparisonView'
import { streamPlan, isComparisonResult, type PlanResult } from './lib/stream'

function App() {
  const [steps, setSteps] = useState<TraceStep[]>([])
  const [result, setResult] = useState<PlanResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(query: string) {
    setSteps([])
    setResult(null)
    setError(null)
    setLoading(true)

    try {
      for await (const event of streamPlan(query)) {
        if (event.type === 'agent_start') {
          setSteps((prev) => [
            ...prev,
            {
              callId: event.call_id,
              agent: event.agent,
              detail: event.detail,
              status: 'running',
            },
          ])
        } else if (event.type === 'agent_result') {
          setSteps((prev) =>
            prev.map((s) =>
              s.callId === event.call_id ? { ...s, status: 'done', summary: event.summary } : s,
            ),
          )
        } else if (event.type === 'done') {
          setResult(event.plan)
        } else if (event.type === 'error') {
          setError(event.message)
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-full bg-neutral-50 dark:bg-neutral-950 px-4 py-16">
      <header className="mx-auto mb-10 max-w-2xl text-center">
        <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
          Toronto Sports Fan Concierge
        </h1>
        <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
          Tell us what you're after — a specialist team of agents plans your night.
        </p>
      </header>

      <main className="space-y-6">
        <RequestBar onSubmit={handleSubmit} disabled={loading} />

        <AgentTrace steps={steps} />

        {error && (
          <div className="w-full max-w-2xl mx-auto rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 px-4 py-3 text-sm text-red-700 dark:text-red-300">
            {error}
          </div>
        )}

        {result &&
          (isComparisonResult(result) ? (
            <ComparisonView comparison={result} />
          ) : (
            <PlanCard plan={result} />
          ))}
      </main>
    </div>
  )
}

export default App

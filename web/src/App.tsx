import { useRef, useState } from 'react'
import { RequestBar } from './components/RequestBar'
import { AgentTrace, type TraceStep } from './components/AgentTrace'
import { PlanCard } from './components/PlanCard'
import { ComparisonView } from './components/ComparisonView'
import {
  streamPlan,
  isComparisonResult,
  type GameNightPlan,
  type PlanResult,
} from './lib/stream'

function App() {
  const [steps, setSteps] = useState<TraceStep[]>([])
  const [result, setResult] = useState<PlanResult | null>(null)
  const [partialPlan, setPartialPlan] = useState<GameNightPlan | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Tracks distinct find_games calls seen this run and whether progressive rendering
  // has been suppressed -- refs, not state, because they're read/written synchronously
  // within a single streamPlan loop iteration and don't need to trigger re-renders
  // themselves (the state they gate does).
  const findGamesCallIds = useRef(new Set<string>())
  const partialSuppressed = useRef(false)

  async function handleSubmit(query: string) {
    setSteps([])
    setResult(null)
    setPartialPlan(null)
    setError(null)
    setLoading(true)
    findGamesCallIds.current = new Set()
    partialSuppressed.current = false

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

          if (event.agent === 'find_games') {
            findGamesCallIds.current.add(event.call_id)
            if (findGamesCallIds.current.size > 1 && !partialSuppressed.current) {
              // A second concurrent find_games call means this is a compare-mode
              // request -- partial rendering can't attribute results to the right
              // option until the final ComparisonResult assigns labels, so bail out
              // to the existing "wait for done" behavior instead of showing a
              // garbled single card mixing both options.
              partialSuppressed.current = true
              setPartialPlan(null)
            }
          }
        } else if (event.type === 'agent_result') {
          setSteps((prev) =>
            prev.map((s) =>
              s.callId === event.call_id ? { ...s, status: 'done', summary: event.summary } : s,
            ),
          )

          if (!partialSuppressed.current && event.data) {
            if (event.agent === 'find_games' && 'games' in event.data) {
              const game = event.data.games[0] ?? null
              setPartialPlan((prev) => ({
                game,
                seating: prev?.seating ?? [],
                dining: prev?.dining ?? [],
                getting_there: prev?.getting_there ?? [],
                summary: prev?.summary ?? '',
              }))
            } else if (event.agent === 'recommend_seating' && 'seating' in event.data) {
              const seating = event.data.seating
              setPartialPlan((prev) =>
                prev
                  ? { ...prev, seating }
                  : { game: null, seating, dining: [], getting_there: [], summary: '' },
              )
            } else if (event.agent === 'local_experience' && 'dining' in event.data) {
              const { dining, getting_there } = event.data
              setPartialPlan((prev) =>
                prev
                  ? { ...prev, dining, getting_there }
                  : { game: null, seating: [], dining, getting_there, summary: '' },
              )
            }
          }
        } else if (event.type === 'done') {
          setResult(event.plan)
          setPartialPlan(null)
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

  // The final composed result always wins once it's in; a partial plan is only a
  // stand-in while streaming (and never shown for compare-mode requests -- see the
  // partialSuppressed guard above). The game shown in the partial plan is
  // find_games's top pick; the coordinator's final choice in `result` is
  // authoritative and can occasionally differ once the full plan lands.
  const displayResult = result ?? (partialPlan?.game ? partialPlan : null)

  return (
    <div className="min-h-full bg-transparent px-4 py-16">
      <header className="mx-auto mb-10 max-w-2xl text-center">
        <h1 className="text-2xl font-semibold text-linear-text">Toronto Sports Fan Concierge</h1>
        <p className="mt-2 text-sm text-linear-text-tertiary">
          Tell us what you're after — a specialist team of agents plans your night.
        </p>
      </header>

      <main className="space-y-6">
        <RequestBar onSubmit={handleSubmit} disabled={loading} />

        <AgentTrace steps={steps} />

        {error && (
          <div className="w-full max-w-2xl mx-auto rounded-lg border border-red-900/60 bg-red-950/30 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {displayResult &&
          (isComparisonResult(displayResult) ? (
            <ComparisonView comparison={displayResult} />
          ) : (
            <PlanCard plan={displayResult} />
          ))}
      </main>
    </div>
  )
}

export default App

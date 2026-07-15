export interface GamePick {
  team: string
  league: string
  opponent: string
  date: string
  time: string
  venue: string
  why: string
}

export interface SeatingOption {
  tier: string
  price_range: string
  vibe: string
  best_for: string
}

export interface LocalTip {
  name: string
  category: string
  detail: string
}

export interface GameNightPlan {
  game: GamePick | null
  seating: SeatingOption[]
  dining: LocalTip[]
  getting_there: LocalTip[]
  summary: string
}

export interface PlanOption {
  label: string
  plan: GameNightPlan
}

export interface ComparisonResult {
  options: PlanOption[]
  recommendation: string
}

export type PlanResult = GameNightPlan | ComparisonResult

export function isComparisonResult(result: PlanResult): result is ComparisonResult {
  return 'options' in result
}

export type PlanEvent =
  | { type: 'agent_start'; agent: string; call_id: string; detail: string | null }
  | { type: 'agent_result'; agent: string; call_id: string; summary: string }
  | { type: 'done'; plan: PlanResult }
  | { type: 'error'; message: string }

/**
 * POSTs the fan's query to /api/plan and yields each SSE event as it arrives.
 * The endpoint is a POST, so we parse the text/event-stream body manually
 * (the browser's EventSource is GET-only) via fetch + ReadableStream.
 */
export async function* streamPlan(query: string): AsyncGenerator<PlanEvent> {
  const response = await fetch('/api/plan', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ query }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE events are separated by a blank line; each line of interest starts with "data: ".
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''

    for (const part of parts) {
      const line = part.split('\n').find((l) => l.startsWith('data: '))
      if (!line) continue
      const json = line.slice('data: '.length)
      yield JSON.parse(json) as PlanEvent
    }
  }
}

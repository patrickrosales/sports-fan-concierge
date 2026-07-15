# Toronto Sports Fan Concierge — Multi-Agent Demo Build Plan

## Context

**Goal:** Build a small, polished, creatively-impressive full-stack app for a technical interview, showcasing
**multi-agent orchestration with Pydantic AI** and Claude, with a clean Linear-style React front-end whose
standout feature is a **live agent-trace UI** — you *watch* specialist agents get called and hand back results.

**What it is — "Toronto Sports Fan Concierge":** A fan types a natural request ("I want to catch a Raptors game
next week, good seats, somewhere to eat nearby, and how to get there without driving"). A **coordinator agent**
routes the request to specialist sub-agents that each assemble part of a personalized **game-night plan**:
- **Schedule Agent** — upcoming games across 8 Toronto-area teams (Blue Jays, Maple Leafs, Raptors,
  Toronto FC, Argonauts, Marlies, Raptors 905, Toronto Tempo)
- **Venue Agent** — seating options + arena/stadium food & amenities
- **Local Experience Agent** — nearby restaurants + transit/pre-game tips

The coordinator composes the sub-agents' outputs into one friendly, structured game-night plan. The creative
hook: it feels like a concierge team collaborating, and the UI shows each agent "speaking up" live.

**Why it's a strong demo:** multi-agent orchestration is impressive to *watch*; the domain is delightful and
concrete; and it exercises real full-stack engineering (typed agents, tool-calling, streaming, a live event
UI). The app is the demo; the build is the story about how you use AI coding tools + a modern agent framework.

## Stack (decided with the user)
- **Backend:** Python + **FastAPI** + **Pydantic AI** + Claude (`anthropic:claude-sonnet-4-6`).
- **Frontend:** Vite + React + TS + Tailwind, Linear-style minimal UI. Two separate services.
- **Data (hybrid, decided):** seed JSON for **schedule + venue** (reliable, offline, deterministic core);
  **live `web_search`** (Claude built-in server tool) only inside the **Local Experience Agent** for
  restaurants/transit. Best-of-both: the core always works in a live demo, with a touch of real-web flair.
- **Orchestration (decided):** **coordinator via agent delegation** — each specialist is a sub-agent the
  coordinator invokes from inside a `@coordinator.tool` function; Claude decides which specialists to call
  based on the request. The resulting tool-call trace is exactly what the UI streams.

## Architecture

```
web/ (Vite + React + TS + Tailwind)
┌────────────────────────────────────────────────────────────────────────┐
│  RequestBar (the ask)                                                  │
│  AgentTrace (live steps, keyed by call_id)                             │
│  PlanCard / ComparisonView (final result)                              │
└────────────────────────────────────────────────────────────────────────┘
     │  POST /api/plan (query)                        ▲
     ▼                                                │  SSE events
api/ (FastAPI + Pydantic AI + Claude)
┌────────────────────────────────────────────────────────────────────────┐
│  POST /api/plan (SSE)                                                  │
│         │                                                              │
│         ▼                                                              │
│  coordinator = Agent(                                                  │
│      instructions, deps,                                               │
│      output_type=[GameNightPlan, ComparisonResult],                    │
│  )                                                                     │
│         │                                                              │
│         │  @coordinator.tool  (only the tools the request needs)       │
│         ├──────────────────┬───────────────────────┬─────────────────┐ │
│         ▼                  ▼                       ▼                 │ │
│    find_games()    recommend_seating()    local_experience()         │ │
│         │                  │                       │                 │ │
│         ▼                  ▼                       ▼                 │ │
│  ┌─────────────┐    ┌─────────────┐     ┌────────────────────────┐   │ │
│  │  Schedule   │    │   Venue     │     │  Local Experience      │   │ │
│  │  Agent      │    │   Agent     │     │  Agent                 │   │ │
│  └──────┬──────┘    └──────┬──────┘     └───────────┬────────────┘   │ │
│         │                  │                        │                │ │
│         ▼                  ▼                        ▼                │ │
│  ┌─────────────────────────────────┐       ┌───────────────────────┐ │ │
│  │ data/games.json, venues.json    │       │ Claude web_search     │ │ │
│  │ (seed, deterministic)           │       │ (live)                │ │ │
│  └─────────────────────────────────┘       └───────────────────────┘ │ │
└──────────────────────────────────────────────────────────────────────┘─┘
```

The coordinator calls its three delegation tools based on what the request actually needs -- not a fixed
pipeline. Each call surfaces as its own `agent_start` → `agent_result` pair over SSE (via
`run_stream_events()`), correlated by a unique `call_id`, followed by a final `done` event carrying the
`GameNightPlan` or `ComparisonResult`.

For a **compare** request ("Raptors or Leafs this weekend?"), the coordinator calls `find_games` (and
often `recommend_seating`/`local_experience`) once per option -- sometimes concurrently -- and returns a
`ComparisonResult` instead of a single `GameNightPlan`. See "Enhancement: Compare Mode" below.

## Pydantic AI specifics (verified against current docs; note churn)
- **Agents:** `Agent('anthropic:claude-sonnet-4-6', instructions=..., deps_type=..., output_type=...)`.
- **Structured output:** each sub-agent returns a Pydantic `BaseModel` via `output_type=` (validated, with
  auto-retry on invalid output). Coordinator's final `output_type` = a `GameNightPlan` model.
- **Agent delegation (the multi-agent core):** a coordinator `@tool` runs a sub-agent and **shares usage** —
  `result = await schedule_agent.run(prompt, deps=..., usage=ctx.usage)`; return `result.output`. Passing
  `usage=ctx.usage` rolls sub-agent token usage into the parent run.
- **Live trace via streaming:** drive the coordinator with **`agent.run_stream_events(...)`** and forward
  `FunctionToolCallEvent` (a specialist started) and `FunctionToolResultEvent` (it finished, with output)
  to the browser over SSE. This is the exact signal the AgentTrace UI renders. (`agent.iter()` is the
  fallback if finer node-level control is needed.)
- **Tools + deps:** `@agent.tool` functions receive `RunContext[Deps]`; seed data (loaded JSON) is injected
  via `deps` so tools query it without globals. Local agent additionally uses Claude's built-in `web_search`.
- ⚠️ **Doc churn:** Pydantic AI docs recently reorganized under `pydantic.dev/docs/ai/...` and some paths
  404. During implementation, re-verify the exact delegation + `run_stream_events` signatures against the
  live docs (or the installed package's source) before finalizing — do not hard-trust these snippets.

## Data contract
- Request: `{ query: string }`
- SSE events (to browser): `{type:'agent_start', agent}`, `{type:'agent_result', agent, summary}`,
  `{type:'done', plan: GameNightPlan}`, `{type:'error', message}`
- `GameNightPlan` (Pydantic): `{ game: {teams, date, venue}, seating: [...], dining: [...],
  getting_there: [...], summary: string }` — every list item typed.

## Build steps
1. **Scaffold** `api/` (FastAPI + `pydantic-ai`, `uvicorn`, run via `uv` or venv) and `web/` (Vite React-TS +
   Tailwind). Root `README.md`; `.env.example` with `ANTHROPIC_API_KEY=`. Vite proxy `/api` → :8000.
2. **Seed data:** `data/games.json` (a handful of upcoming games per team) + `data/venues.json`
   (downtown Toronto arena/stadium seating tiers + food, generically named). Small, curated, realistic.
3. **Sub-agents (one at a time, each independently runnable):** `schedule_agent`, `venue_agent`,
   `local_agent`. Each: its own `Agent` + `output_type` model + tools over deps (local agent adds
   `web_search`). Unit-test each in isolation first.
4. **Coordinator:** `Agent` with a `GameNightPlan` output_type and three `@tool` delegation functions that
   call the sub-agents with `usage=ctx.usage`. Get a full non-streaming `run()` working end-to-end.
5. **Stream it:** wrap the coordinator in `run_stream_events()`, map events → the SSE schema above, expose
   `POST /api/plan` as `text/event-stream`. Add a refusal/error guard + typed error handling.
6. **Frontend:** RequestBar + AgentTrace (renders agent_start/agent_result as a live checklist with
   spinners → checks) + PlanCard (the final structured plan). Linear-style: neutral grays, one accent,
   generous whitespace, subtle borders, no gradients; wide content scrolls in its own container.
7. **Polish + demo script:** 3 one-click example prompts ("Raptors night with dinner", "Leafs + transit
   from downtown", "weekend doubleheader") so the demo is instant and reliably shows multi-agent routing.

## Critical files
- `api/app/main.py` — FastAPI app + `/api/plan` SSE route + event mapping
- `api/app/coordinator.py` — coordinator Agent + the three delegation `@tool`s (the multi-agent core)
- `api/app/agents/{schedule,venue,local}.py` — the three specialist sub-agents + their output models
- `api/app/models.py` — Pydantic output models (`GameNightPlan`, per-agent outputs) + deps dataclass
- `api/app/data.py` — load seed JSON into deps
- `api/data/{games,venues}.json` — seed data
- `web/src/App.tsx`; `web/src/components/{RequestBar,AgentTrace,PlanCard}.tsx`;
  `web/src/lib/stream.ts` (SSE consumer)
- `README.md`, `.env.example`

## Verification (end-to-end, not just types)
- **Run both:** `api` on :8000 (`uvicorn`), `web` on :5173; confirm the proxy works.
- **Sub-agents in isolation:** each returns a valid typed output for a representative prompt before wiring
  the coordinator (catches schema/tool bugs early).
- **Happy path:** submit an example prompt; confirm the AgentTrace shows specialists starting/finishing live
  and the PlanCard renders a coherent, correctly-typed game-night plan referencing seed games/venues.
- **Multi-agent routing:** a schedule-only prompt ("when do the Leafs play next?") should call fewer
  specialists than a full-plan prompt — confirming the coordinator routes dynamically, not a fixed pipeline.
- **Live-web slice:** confirm the Local Agent's `web_search` returns real nearby spots (and degrades to a
  graceful message if search errors — the seed core still produces a plan).
- **Failure states:** unset `ANTHROPIC_API_KEY` → clean error surfaced in UI (no crash); empty query →
  validation error.
- **UI check:** run + screenshot; confirm the Linear-style look holds and the body never scrolls horizontally.

## Interview talking points this build creates (keep notes as you go)
- Multi-agent orchestration via **agent delegation** and why the coordinator-routes pattern beats a fixed
  pipeline (the model decides which specialists are relevant).
- **Typed, validated agent output** with Pydantic models + auto-retry — reliability of LLM output.
- **Streaming the agent event loop** (`run_stream_events` → SSE) to make agent collaboration visible.
- **Dependency injection** (`RunContext` + deps) for clean, testable tools over seed data.
- **Hybrid data** decision: deterministic seed core + a live-web slice — reliability vs. realism tradeoff.
- Secret handling (Claude key server-side only, never in the browser).
- How AI coding tools helped: scaffolding FastAPI/React boilerplate, the SSE event plumbing, and verifying
  fast-moving Pydantic AI APIs against live docs — while you owned the agent design and the domain modeling.

## Enhancement: Compare Mode

**What it does:** a request naming two or more options ("Raptors or Leafs this weekend — which is the
better night out?") makes the coordinator plan *both* in full — schedule, seating, dining, transit — and
return a side-by-side comparison with a recommendation, instead of forcing a single pick. Fully
coordinator-driven (no separate "compare" endpoint or UI toggle): the same instructions that tell the
coordinator when to call which specialists now also tell it when to fan out per-option.

**Output shape:** the coordinator's `output_type` is `[GameNightPlan, ComparisonResult]` — a *list* of
alternative output types (Pydantic AI's actual union syntax; a Python `X | Y` type annotation does not
work here, confirmed by reading `pydantic_ai/output.py`'s `OutputSpec` definition and by constructing an
`Agent` with a list `output_type` directly). Claude picks whichever shape fits the request; single-option
requests are unaffected and still return a plain `GameNightPlan`.

```python
class PlanOption(BaseModel):
    label: str          # e.g. "Raptors"
    plan: GameNightPlan

class ComparisonResult(BaseModel):
    options: list[PlanOption]
    recommendation: str
```

**The concurrency bug this surfaced (and why the fix was necessary, not defensive):** under Pydantic AI's
default `end_strategy='graceful'`, function tools called in the same turn run **in parallel** via asyncio
(confirmed by reading `pydantic_ai._agent_graph.process_tool_calls` directly). Live-tested against the
running app: a compare prompt produced two concurrent `find_games` calls whose *results resolved out of
order* (the second call's result arrived before the first's). The original SSE/trace design keyed
everything by tool name alone (`agent_start`/`agent_result` payloads only carried `"agent": tool_name`;
the frontend matched `s.agent === event.agent && s.status === 'running'`) — with concurrent calls to the
same tool, a result could get attributed to the wrong trace row. The fix threads each call's unique
`tool_call_id` through the SSE payload as `call_id`, and the frontend keys trace steps by `call_id` instead
of by agent name, so concurrent calls to the same specialist never collide regardless of completion order.

**Caveat — not deterministic:** the same compare-style request doesn't always produce concurrent calls.
A slightly different phrasing of the identical request was observed to produce a single `find_games` call
with both teams folded into one request string instead of two parallel calls. Both outcomes are handled
correctly (the `call_id` keying works either way), but the "watch two specialist teams work at once" demo
moment isn't guaranteed on every phrasing — worth knowing before relying on it live.

**Trace labeling:** delegation tools take free-text args (`find_games(request: str)`, not a structured team
field), so trace rows are labeled with that raw request text (e.g. "Schedule Agent — Toronto Raptors home
game this weekend") rather than a parsed team name — simpler, and matches what the coordinator actually
sends in practice.

## Enhancement: Speed

**Problem:** live testing showed full runs regularly taking 60-160+ seconds, almost entirely inside the
Local Experience Agent's `web_search` call. A full compare-mode run was directly timed at 161s -- too slow
for a live demo. The coordinator's delegation calls already run concurrently where the model chooses to
(confirmed live), so there was no free win from restructuring the coordinator itself.

**Fixes shipped (`api/app/cache.py`, `api/app/coordinator.py`, `api/app/agents/local.py`,
`api/app/main.py`, `web/src/App.tsx`):**
- **Venue-keyed cache** for `local_experience` results. Keyed on `venue_name` alone, not the
  LLM-generated `neighbourhood` argument (which isn't stable across calls for the same venue). A per-key
  `asyncio.Lock` means concurrent calls to the same venue (common in compare-mode requests) share one
  in-flight fetch instead of duplicating a live search. Measured: 96s cold → 31s warm single-plan run;
  161s → 36s full compare-mode run.
- **Progressive rendering**: `agent_result` SSE events now carry a `data` field with the sub-agent's full
  typed output, so the frontend renders the game + seating as soon as they're ready instead of waiting for
  the final `done` event. Guarded against compare-mode: if a second `find_games` `agent_start` is seen
  (the compare-mode tell), partial rendering is suppressed for the rest of the run to avoid showing a
  garbled single card mixing two options' data.
- **Trimmed `web_search` `max_uses`** from 3 to 2. `search_context_size` was empirically tested at `low`
  vs. the default `medium` and left at `medium` -- `low` measured *slower* in a direct A/B test, an
  unintuitive but empirically-verified result worth remembering before "optimizing" it again.

## Enhancement: Real Venues

**What changed:** seed data (`api/data/games.json`, `api/data/venues.json`) now uses real, verified
venue names instead of the earlier generic/fictional ones (Center Court Arena, Downtown Dome, Waterfront
Pitch), and the team roster expanded from 5 to 8: Blue Jays, Maple Leafs, Raptors, Toronto FC, Argonauts,
Marlies, Raptors 905, and Toronto Tempo.

This is an intentional reversal of an earlier explicit instruction in this project to remove all
MLSE-related references and keep venues generic -- confirmed with the user before implementing, since 7 of
the 8 teams are MLSE-owned/operated properties. Opponents, dates, and times remain plausible fiction, not
reconstructed real fixtures -- only the venue/team identities are real.

**Verified venue mapping** (via live web search, not assumed from training data -- Toronto Tempo is a 2026
WNBA expansion team and Raptors 905's venue was genuinely uncertain going in):

| Team | League | Venue |
|---|---|---|
| Blue Jays | MLB | Rogers Centre |
| Maple Leafs, Raptors | NHL, NBA | Scotiabank Arena |
| Toronto FC, Argonauts | MLS, CFL | BMO Field |
| Marlies, Toronto Tempo | AHL, WNBA | Coca-Cola Coliseum |
| Raptors 905 | NBA G League | Mississauga Sports and Entertainment Centre |

Real venues collapsed to 5 shared venues (down from 8 fictional 1:1 venues), which is a bonus for the
venue-keyed cache from the Speed enhancement above -- a query for the Leafs now warms the cache for the
Raptors too, since they share Scotiabank Arena.

**The one non-obvious fix this required:** Mississauga Sports and Entertainment Centre is not in Toronto
proper. The Local Experience Agent's prompt and instructions previously hardcoded "Toronto" and "TTC
subway, streetcar, GO Transit" as the default transit context, which would have produced wrong transit
advice for Raptors 905 games. Both `coordinator.py`'s `local_experience` prompt construction and
`agents/local.py`'s instructions were made region-agnostic -- the venue's `neighbourhood` field (from
`venues.json`) now carries the correct regional context instead of the prompt assuming Toronto/TTC.

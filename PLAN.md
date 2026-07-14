# Toronto Sports Fan Concierge — Multi-Agent Demo Build Plan

## Context

**Goal:** Build a small, polished, creatively-impressive full-stack app for a technical interview, showcasing
**multi-agent orchestration with Pydantic AI** and Claude, with a clean Linear-style React front-end whose
standout feature is a **live agent-trace UI** — you *watch* specialist agents get called and hand back results.

**What it is — "Toronto Sports Fan Concierge":** A fan types a natural request ("I want to catch a Raptors game
next week, good seats, somewhere to eat nearby, and how to get there without driving"). A **coordinator agent**
routes the request to specialist sub-agents that each assemble part of a personalized **game-night plan**:
- **Schedule Agent** — upcoming games across Toronto's major teams (Raptors, Maple Leafs, Blue Jays, TFC, Argonauts)
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
web/ (Vite + React + TS + Tailwind)              api/ (FastAPI + Pydantic AI + Claude)
┌──────────────────────────────┐                 ┌───────────────────────────────────────────┐
│ RequestBar  (fan's ask)       │  POST /api/plan  │ /plan  (SSE)                              │
│ AgentTrace  (live steps)      │ ◀──SSE events──  │  coordinator = Agent(instructions, deps)  │
│   ▸ Schedule Agent  ✓          │                 │   @coordinator.tool find_games(...)  ──┐   │
│   ▸ Venue Agent     ✓          │                 │   @coordinator.tool venue_options(...) │   │
│   ▸ Local Agent     …          │                 │   @coordinator.tool local_tips(...)    │   │
│ PlanCard    (final plan)       │                 │        each calls a sub-Agent.run(     │   │
└──────────────────────────────┘                 │            ..., usage=ctx.usage)  ◀─────┘   │
                                                  │  run_stream_events() → SSE → browser       │
                                                  └───────────────────────────────────────────┘
                                    seed: data/games.json, venues.json   live: web_search (local agent)
```

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

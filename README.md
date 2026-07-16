# Sports Fan Concierge

A multi-agent demo: tell it what kind of game night you're after, and a coordinator agent
delegates to three specialists — a **Schedule Agent**, a **Venue Agent**, and a **Local
Experience Agent** (which uses live web search) — to assemble a personalized game-night plan.
The front-end shows the specialists collaborating live as they work.

Built with **Pydantic AI** (typed, validated agent output) + **Claude** on the backend, and a
clean **React + Tailwind** front-end that streams the agent trace over Server-Sent Events.

See [`PLAN.md`](./PLAN.md) for the full design and architecture writeup.

## Prerequisites

- Python 3.10+
- Node 18+
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

```bash
# 1. Add your API key
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 2. Backend
cd api
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Frontend
cd ../web
npm install
```

## Run

Two terminals, from the repo root:

```bash
# Terminal 1 — API on :8000
lsof -ti :8000 | xargs kill -9 2>/dev/null; api/.venv/bin/uvicorn app.main:app --port 8000 --app-dir api --reload

# Terminal 2 — web app on :5173 (proxies /api -> :8000)
cd web && npm run dev
```

Open http://localhost:5173.

## Manual backend check (no browser needed)

```bash
api/.venv/bin/python api/test_run.py
```

Runs the coordinator once directly and prints the composed plan, then again with the
live specialist trace streamed to your terminal.

## Stack

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


## How it works

- `api/app/agents/` — the three specialist agents (`schedule`, `venue`, `local`), each a
  Pydantic AI `Agent` with a typed `output_type` and its own tools.
- `api/app/coordinator.py` — the coordinator agent. Its `@tool` functions delegate to the
  specialists (`sub_agent.run(..., usage=ctx.usage)`), so Claude decides which specialists a
  given request actually needs — this isn't a fixed pipeline.
- `api/app/main.py` — a FastAPI endpoint that drives the coordinator with
  `run_stream_events()` and forwards each specialist's start/finish as a Server-Sent Event.
- `api/data/` — seed schedule + venue data (reliable, deterministic core). The Local
  Experience Agent is the one live-web slice, via Claude's built-in `web_search` tool.
- `web/src/` — the React front-end: `RequestBar`, `AgentTrace` (the live specialist
  checklist), and `PlanCard` (the final plan), wired up with a small SSE consumer.

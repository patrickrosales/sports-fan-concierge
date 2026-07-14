# Toronto Sports Fan Concierge

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
api/.venv/bin/uvicorn app.main:app --port 8000 --app-dir api --reload

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

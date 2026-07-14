"""FastAPI app: streams the coordinator's multi-agent run to the browser over SSE.

Event protocol (each SSE ``data:`` line is a JSON object):
    {"type": "agent_start",  "agent": <tool name>}
    {"type": "agent_result", "agent": <tool name>, "summary": <one-liner>}
    {"type": "done",         "plan": <GameNightPlan as JSON>}
    {"type": "error",        "message": <string>}

Only the three delegation tools are surfaced -- internal machinery (e.g. the
structured-output tool, sub-agent internals) never reaches the trace.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from pydantic_ai import AgentRunResultEvent
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ToolReturnPart,
)

from .coordinator import coordinator
from .data import load_deps
from .models import LocalResult, ScheduleResult, VenueResult
from .settings import has_api_key

# The three delegation tools = the specialists the AgentTrace UI renders.
DELEGATION_TOOLS = {"find_games", "recommend_seating", "local_experience"}

app = FastAPI(title="Toronto Sports Fan Concierge")

# The Vite dev server proxies /api, so CORS isn't strictly needed in dev --
# but allowing localhost keeps direct access working too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _result_summary(content: object) -> str:
    """One-line summary of a specialist's output for the trace UI."""
    if isinstance(content, ScheduleResult):
        if content.games:
            g = content.games[0]
            return f"Top pick: {g.team} vs {g.opponent} on {g.date} @ {g.venue}"
        return content.note or "No matching games found"
    if isinstance(content, VenueResult):
        tiers = ", ".join(s.tier for s in content.seating[:3])
        return f"{content.venue}: {tiers}" if tiers else content.venue
    if isinstance(content, LocalResult):
        return f"{len(content.dining)} dining spots, {len(content.getting_there)} transit tips"
    return "finished"


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "api_key_configured": has_api_key()}


@app.post("/api/plan")
async def plan(req: PlanRequest) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        if not has_api_key():
            yield _sse({"type": "error", "message": "Server is missing ANTHROPIC_API_KEY."})
            return
        try:
            deps = load_deps()
            async with coordinator.run_stream_events(req.query, deps=deps) as events:
                async for event in events:
                    if (
                        isinstance(event, FunctionToolCallEvent)
                        and event.part.tool_name in DELEGATION_TOOLS
                    ):
                        yield _sse({"type": "agent_start", "agent": event.part.tool_name})
                    elif (
                        isinstance(event, FunctionToolResultEvent)
                        and isinstance(event.part, ToolReturnPart)
                        and event.part.tool_name in DELEGATION_TOOLS
                    ):
                        yield _sse(
                            {
                                "type": "agent_result",
                                "agent": event.part.tool_name,
                                "summary": _result_summary(event.part.content),
                            }
                        )
                    elif isinstance(event, AgentRunResultEvent):
                        plan_model = event.result.output
                        yield _sse({"type": "done", "plan": plan_model.model_dump()})
        except Exception as exc:  # surface anything (rate limit, refusal, network) cleanly
            yield _sse({"type": "error", "message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

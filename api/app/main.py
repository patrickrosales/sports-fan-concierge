"""FastAPI app: streams the coordinator's multi-agent run to the browser over SSE.

Event protocol (each SSE ``data:`` line is a JSON object):
    {"type": "agent_start",  "agent": <tool name>, "call_id": <str>, "detail": <str|null>}
    {"type": "agent_result", "agent": <tool name>, "call_id": <str>, "summary": <one-liner>, "data": <typed sub-result JSON>}
    {"type": "done",         "plan": <GameNightPlan or ComparisonResult as JSON>}
    {"type": "error",        "message": <string>}

``data`` on ``agent_result`` carries the sub-agent's full typed output (a ScheduleResult,
VenueResult, or LocalResult, serialized). The frontend uses it to progressively render a
partial plan as pieces arrive, rather than waiting for the final ``done`` event -- the
``local_experience`` call alone can take 60s+, so showing the game/seating as soon as
they're ready meaningfully improves perceived speed even though total latency is
unchanged. ``summary`` remains the one-liner the AgentTrace UI shows regardless.

Only the three delegation tools are surfaced -- internal machinery (e.g. the
structured-output tool, sub-agent internals) never reaches the trace.

``call_id`` is the tool call's unique ``tool_call_id``. It's required for correctness,
not just nicety: the coordinator can (and for compare-mode requests, does) call the same
delegation tool multiple times concurrently in one turn -- e.g. two ``find_games`` calls
running in parallel, one per team being compared. Their results can resolve out of order.
Keying purely by tool name (as an earlier version of this endpoint did) would let a second
call's result get attributed to the first call's still-running trace step. ``call_id``
keeps each call's start/result pair distinct no matter the completion order.
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
from .links import maps_search_url, ticket_search_url
from .models import ComparisonResult, GameNightPlan, LocalResult, ScheduleResult, VenueResult
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


def _call_detail(event: FunctionToolCallEvent) -> str | None:
    """Short human-readable detail for a delegation call, e.g. which team/venue it's about.

    Delegation tools take free-text args (``request``, ``venue_name``) rather than a
    structured team field, so we surface that text directly instead of trying to parse
    a team name out of it -- it's already specific in practice (e.g. the coordinator
    calls ``find_games`` with "Toronto Raptors home game this weekend").
    """
    args = event.part.args_as_dict()
    detail = args.get("request") or args.get("venue_name")
    if not detail:
        return None
    return detail if len(detail) <= 60 else f"{detail[:57]}..."


def _add_links(plan: GameNightPlan) -> GameNightPlan:
    """Fill in venue/ticket/dining links via deterministic templates (see links.py).

    Never LLM-generated -- computed here, after the coordinator's output is final, from
    name strings the specialists already returned.
    """
    if plan.game:
        plan.venue_url = maps_search_url(plan.game.venue)
        plan.ticket_url = ticket_search_url(plan.game.team)
    plan.dining = [tip.model_copy(update={"url": maps_search_url(tip.name)}) for tip in plan.dining]
    return plan


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
                        yield _sse(
                            {
                                "type": "agent_start",
                                "agent": event.part.tool_name,
                                "call_id": event.part.tool_call_id,
                                "detail": _call_detail(event),
                            }
                        )
                    elif (
                        isinstance(event, FunctionToolResultEvent)
                        and isinstance(event.part, ToolReturnPart)
                        and event.part.tool_name in DELEGATION_TOOLS
                    ):
                        content = event.part.content
                        yield _sse(
                            {
                                "type": "agent_result",
                                "agent": event.part.tool_name,
                                "call_id": event.part.tool_call_id,
                                "summary": _result_summary(content),
                                "data": (
                                    content.model_dump()
                                    if isinstance(
                                        content, ScheduleResult | VenueResult | LocalResult
                                    )
                                    else None
                                ),
                            }
                        )
                    elif isinstance(event, AgentRunResultEvent):
                        plan_model = event.result.output
                        if isinstance(plan_model, GameNightPlan):
                            plan_model = _add_links(plan_model)
                        elif isinstance(plan_model, ComparisonResult):
                            for option in plan_model.options:
                                _add_links(option.plan)
                        yield _sse({"type": "done", "plan": plan_model.model_dump()})
        except Exception as exc:  # surface anything (rate limit, refusal, network) cleanly
            yield _sse({"type": "error", "message": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

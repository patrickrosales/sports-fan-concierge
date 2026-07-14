"""Schedule Agent -- finds upcoming Toronto games from the seed schedule."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from ..models import ConciergeDeps, ScheduleResult
from ..settings import MODEL

schedule_agent = Agent(
    MODEL,
    deps_type=ConciergeDeps,
    output_type=ScheduleResult,
    # defer_model_check lets us construct the agent at import time without the
    # API key present; the key is only needed when the agent actually runs.
    defer_model_check=True,
    instructions=(
        "You are the Schedule Agent for a Toronto sports concierge. "
        "Use the `list_games` tool to see upcoming games, then pick the ones that best "
        "match the fan's request (team, date window, or vibe). Return them best-first. "
        "Only include games from the tool's data -- never invent games, dates, or opponents. "
        "If nothing matches well, return an empty list and a short note saying so."
    ),
)


@schedule_agent.tool
def list_games(ctx: RunContext[ConciergeDeps]) -> list[dict]:
    """Return all upcoming Toronto games in the seed schedule."""
    return ctx.deps.games

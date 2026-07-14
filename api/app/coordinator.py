"""Coordinator agent -- the multi-agent core.

The coordinator has three delegation tools, one per specialist sub-agent. Claude
decides which specialists to call based on the fan's request (dynamic routing, not
a fixed pipeline). Each delegation tool runs its sub-agent with ``usage=ctx.usage``
so token usage rolls up into the parent run.

The tool names below (``find_games`` / ``recommend_seating`` / ``local_experience``)
are exactly what the front-end AgentTrace renders as the specialists "speaking up".
"""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from .agents import local_agent, schedule_agent, venue_agent
from .models import ConciergeDeps, GameNightPlan, LocalResult, ScheduleResult, VenueResult
from .settings import MODEL

coordinator = Agent(
    MODEL,
    deps_type=ConciergeDeps,
    output_type=GameNightPlan,
    defer_model_check=True,
    instructions=(
        "You are the concierge coordinator for a Toronto sports fan. "
        "Plan a great game night by delegating to your specialist tools:\n"
        "1. Call `find_games` to choose the best matching game for the request.\n"
        "2. Call `recommend_seating` with that game's venue to get seating + food.\n"
        "3. Call `local_experience` with the venue and neighbourhood for dining + transit.\n"
        "Only call the specialists you actually need for the request -- if the fan only "
        "asks about the schedule, you don't need seating or local tips. "
        "Then compose everything into one warm, concrete game-night plan. "
        "Base the plan strictly on what the specialists return; never invent games, "
        "prices, or venues."
    ),
)


@coordinator.tool
async def find_games(ctx: RunContext[ConciergeDeps], request: str) -> ScheduleResult:
    """Delegate to the Schedule Agent to find upcoming games matching the request."""
    result = await schedule_agent.run(request, deps=ctx.deps, usage=ctx.usage)
    return result.output


@coordinator.tool
async def recommend_seating(
    ctx: RunContext[ConciergeDeps], venue_name: str, preference: str = ""
) -> VenueResult:
    """Delegate to the Venue Agent for seating + food at the given venue."""
    prompt = f"Venue: {venue_name}. Fan preference: {preference or 'no strong preference'}."
    result = await venue_agent.run(prompt, deps=ctx.deps, usage=ctx.usage)
    return result.output


@coordinator.tool
async def local_experience(
    ctx: RunContext[ConciergeDeps], venue_name: str, neighbourhood: str
) -> LocalResult:
    """Delegate to the Local Experience Agent (live web search) for dining + transit."""
    prompt = (
        f"Venue: {venue_name} in the {neighbourhood} area of Toronto. "
        "Find nearby dining and public-transit tips for a game night here."
    )
    # local_agent has no deps_type, so we don't pass deps; we do share usage.
    result = await local_agent.run(prompt, usage=ctx.usage)
    return result.output

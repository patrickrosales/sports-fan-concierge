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
from .cache import get_or_fetch
from .models import (
    ComparisonResult,
    ConciergeDeps,
    GameNightPlan,
    LocalResult,
    ScheduleResult,
    VenueResult,
)
from .settings import MODEL

coordinator = Agent(
    MODEL,
    deps_type=ConciergeDeps,
    output_type=[GameNightPlan, ComparisonResult],
    defer_model_check=True,
    instructions=(
        "You are the concierge coordinator for a Toronto sports fan. "
        "Plan a great game night by delegating to your specialist tools:\n"
        "1. Call `find_games` to choose the best matching game for the request.\n"
        "2. Call `recommend_seating` with that game's venue to get seating + food.\n"
        "3. Call `local_experience` with the venue and neighbourhood for dining + transit.\n"
        "Only call the specialists you actually need for the request -- if the fan only "
        "asks about the schedule, you don't need seating or local tips. "
        "Base every plan strictly on what the specialists return; never invent games, "
        "prices, or venues. If `find_games` returns no matching games (e.g. the team "
        "isn't one we track, or nothing is scheduled), do NOT call the other specialists "
        "or invent a game -- set `game` to null and use `summary` to explain what happened "
        "and which teams/data you do have.\n\n"
        "COMPARISON REQUESTS: if the fan names two or more teams/games to choose between "
        "(e.g. 'Raptors or Leafs this weekend', 'compare a Jays game vs a TFC game'), plan "
        "each option in full -- call `find_games` once per option with a specific request "
        "naming that option (e.g. 'Toronto Raptors home game this weekend'), then run "
        "`recommend_seating`/`local_experience` for each option's game as needed. Return a "
        "`ComparisonResult` with one `PlanOption` per option (a short `label` plus its "
        "`GameNightPlan`) and a `recommendation` explaining which option you'd pick and why. "
        "If an option has no matching game, still include it with `game: null` and a note in "
        "its plan's `summary`, rather than dropping it. For a single-option request, return a "
        "plain `GameNightPlan` as before."
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
    """Delegate to the Local Experience Agent (live web search) for dining + transit.

    Cached by venue_name: the live web_search call is the slowest part of a run, and
    the seed data only has 3 fixed venues, so repeat requests for the same venue (a
    common case in compare-mode requests) reuse the cached result instead of
    re-searching. See cache.py for why the key is venue_name alone.
    """

    async def fetch() -> LocalResult:
        prompt = (
            f"Venue: {venue_name}, in the {neighbourhood} area. "
            "Find nearby dining and public-transit tips for a game night here."
        )
        # local_agent has no deps_type, so we don't pass deps; we do share usage.
        result = await local_agent.run(prompt, usage=ctx.usage)
        return result.output

    return await get_or_fetch(venue_name, fetch)

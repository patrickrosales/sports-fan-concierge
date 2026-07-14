"""Venue Agent -- recommends seating + food for a given venue."""

from __future__ import annotations

from pydantic_ai import Agent, RunContext

from ..models import ConciergeDeps, VenueResult
from ..settings import MODEL

venue_agent = Agent(
    MODEL,
    deps_type=ConciergeDeps,
    output_type=VenueResult,
    defer_model_check=True,
    instructions=(
        "You are the Venue Agent for a Toronto sports concierge. "
        "Use the `get_venue` tool to look up seating tiers and food for the venue named "
        "in the request. Recommend 2-3 seating tiers matched to the fan's budget/intent "
        "(value, best-view, or premium), and call out a few food highlights. "
        "Only use tiers and food that the tool returns -- do not invent options."
    ),
)


@venue_agent.tool
def get_venue(ctx: RunContext[ConciergeDeps], venue_name: str) -> dict:
    """Look up seating tiers, food, and amenities for a venue by name.

    Returns an empty dict if the venue is not in the seed data.
    """
    return ctx.deps.venues.get(venue_name, {})

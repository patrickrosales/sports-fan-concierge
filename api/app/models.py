"""Pydantic output models for the agents, plus the shared deps object.

Every agent returns a typed model via ``output_type=``. Pydantic AI validates the
model's output against these schemas and asks the model to retry if validation
fails -- that's the reliability story for LLM output.
"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Per-agent output models
# ---------------------------------------------------------------------------
class GamePick(BaseModel):
    """A single game the Schedule Agent surfaced."""

    team: str = Field(description="The Toronto team playing (e.g. Raptors, Blue Jays).")
    league: str = Field(description="League label, e.g. 'NBA' or 'MLB'.")
    opponent: str = Field(description="The opposing team.")
    date: str = Field(description="Game date, ISO format YYYY-MM-DD.")
    time: str = Field(description="Local start time, 24h HH:MM.")
    venue: str = Field(description="Venue name where the game is played.")
    why: str = Field(description="One sentence on why this game fits the fan's request.")


class ScheduleResult(BaseModel):
    """Output of the Schedule Agent."""

    games: list[GamePick] = Field(description="Matching upcoming games, best first.")
    note: str = Field(default="", description="Optional note if nothing matched well.")


class SeatingOption(BaseModel):
    tier: str
    price_range: str
    vibe: str
    best_for: str


class VenueResult(BaseModel):
    """Output of the Venue Agent."""

    venue: str = Field(description="Venue name.")
    seating: list[SeatingOption] = Field(description="Recommended seating tiers for this fan.")
    food_highlights: list[str] = Field(description="A few food/amenity highlights to call out.")


class LocalTip(BaseModel):
    name: str = Field(description="Place or option name.")
    category: str = Field(description="e.g. 'restaurant', 'transit', 'pre-game'.")
    detail: str = Field(description="One-line why/what, kept concrete.")


class LocalResult(BaseModel):
    """Output of the Local Experience Agent."""

    dining: list[LocalTip] = Field(description="Nearby food options.")
    getting_there: list[LocalTip] = Field(description="Transit / arrival tips (no driving where possible).")


# ---------------------------------------------------------------------------
# Coordinator (final) output model
# ---------------------------------------------------------------------------
class GameNightPlan(BaseModel):
    """The composed, fan-facing game-night plan the coordinator returns."""

    game: GamePick | None = Field(
        default=None,
        description="The chosen game for the plan, or null if no matching game was found.",
    )
    seating: list[SeatingOption] = Field(default_factory=list, description="Suggested seating options.")
    dining: list[LocalTip] = Field(default_factory=list, description="Where to eat nearby.")
    getting_there: list[LocalTip] = Field(
        default_factory=list, description="How to get there without driving."
    )
    summary: str = Field(
        description=(
            "A warm, 2-3 sentence wrap-up of the night for the fan. "
            "If no game was found, a friendly explanation of why and what teams/data are available instead."
        )
    )


# ---------------------------------------------------------------------------
# Dependencies injected into agent tools via RunContext
# ---------------------------------------------------------------------------
@dataclass
class ConciergeDeps:
    """Seed data made available to agent tools (no globals)."""

    games: list[dict]
    venues: dict[str, dict]

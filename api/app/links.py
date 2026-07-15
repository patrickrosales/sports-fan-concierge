"""Deterministic link builders.

Every link in the app is generated from a trusted name string already held in our own
data or a specialist's typed output -- never written by an LLM. This sidesteps URL
hallucination entirely: no citation/URL field exists on Pydantic AI's ``WebSearchTool``,
and even if it did, letting a model emit a URL string risks a plausible-looking wrong
link (worst case for a ticket-purchase link).
"""

from __future__ import annotations

from urllib.parse import quote_plus


def maps_search_url(place: str) -> str:
    """A Google Maps search URL for a place name (venue, restaurant, etc.)."""
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(place)}"


def ticket_search_url(team: str) -> str:
    """A Ticketmaster search URL for a team name."""
    return f"https://www.ticketmaster.ca/search?q={quote_plus(team)}"

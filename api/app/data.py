"""Load the seed JSON into a ConciergeDeps object."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .models import ConciergeDeps

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_deps() -> ConciergeDeps:
    """Read games.json + venues.json once and cache the result."""
    games = json.loads((DATA_DIR / "games.json").read_text(encoding="utf-8"))
    venues = json.loads((DATA_DIR / "venues.json").read_text(encoding="utf-8"))
    return ConciergeDeps(games=games, venues=venues)

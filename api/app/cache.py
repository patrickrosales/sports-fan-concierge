"""Process-lifetime cache for the Local Experience Agent's live web_search results.

The seed data only has 3 venues, so the live-search space is small and fixed --
caching by venue turns repeat queries (including both options in many compare-mode
requests, which often resolve to the same venue) into near-instant hits instead of
another ~60-90s web_search call.

Keyed on ``venue_name`` alone, not the coordinator-supplied ``neighbourhood`` -- that
argument is LLM-generated free text and isn't stable across calls for the same venue
(observed directly this session: the coordinator phrases equivalent delegation
requests differently call to call). ``venue_name`` alone also fully determines the
answer, since each seed venue has exactly one neighbourhood.

No TTL: venue seed data doesn't change at runtime, so a cache that resets on server
restart is sufficient.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

_cache: dict[str, T] = {}
_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


async def get_or_fetch(key: str, fetch: Callable[[], Awaitable[T]]) -> T:
    """Return the cached value for ``key``, or await ``fetch()`` once and cache it.

    A per-key lock ensures concurrent callers for the same key (e.g. two compare-mode
    options resolving to the same venue) share one in-flight fetch instead of both
    firing a redundant live search.
    """
    async with _locks[key]:
        if key not in _cache:
            _cache[key] = await fetch()
    return _cache[key]

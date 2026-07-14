"""Manual end-to-end check of the multi-agent core.

Run this AFTER putting your ANTHROPIC_API_KEY in the repo-root .env:

    api/.venv/bin/python api/test_run.py

It runs the coordinator once (non-streaming) and prints the composed GameNightPlan,
then runs it again with streaming to show the live specialist trace. No frontend needed.
"""

from __future__ import annotations

import asyncio

from app.coordinator import coordinator
from app.data import load_deps
from app.settings import has_api_key

DELEGATION_TOOLS = {"find_games", "recommend_seating", "local_experience"}

PROMPT = (
    "I want to catch a Raptors game this fall, good seats but not crazy expensive, "
    "somewhere to grab dinner nearby, and how to get there without driving."
)


async def main() -> None:
    if not has_api_key():
        print("No ANTHROPIC_API_KEY found. Add it to the repo-root .env and re-run.")
        return

    deps = load_deps()

    # 1) Non-streaming: validate the full multi-agent core end to end.
    print("=== non-streaming run ===")
    result = await coordinator.run(PROMPT, deps=deps)
    plan = result.output
    print(f"Game: {plan.game.team} vs {plan.game.opponent} on {plan.game.date} @ {plan.game.venue}")
    print(f"Seating options: {len(plan.seating)} | dining: {len(plan.dining)} | transit: {len(plan.getting_there)}")
    print(f"Summary: {plan.summary}\n")

    # 2) Streaming: show the specialist trace the way the UI will.
    print("=== streaming event trace (delegation tools only) ===")
    from pydantic_ai.messages import FunctionToolCallEvent, FunctionToolResultEvent

    async with coordinator.run_stream_events(PROMPT, deps=deps) as events:
        async for event in events:
            if isinstance(event, FunctionToolCallEvent) and event.part.tool_name in DELEGATION_TOOLS:
                print(f"  -> {event.part.tool_name} started")
            elif isinstance(event, FunctionToolResultEvent) and event.part.tool_name in DELEGATION_TOOLS:
                print(f"  <- {event.part.tool_name} finished")


if __name__ == "__main__":
    asyncio.run(main())

"""Logfire instrumentation for the multi-agent run.

`instrument_pydantic_ai()` patches pydantic-ai's ``Agent`` globally, so the
coordinator run and all three sub-agent runs (Schedule / Venue / Local
Experience) show up as nested spans -- each with its prompts, tool calls, and
token usage. That's the durable trace beyond the live AgentTrace UI.

Gated on a token: ``send_to_logfire="if-token-present"`` means a missing
``LOGFIRE_TOKEN`` is a clean no-op (no warning, no network), so the app runs
unchanged for anyone who hasn't set Logfire up. Set ``LOGFIRE_TOKEN`` (from a
Logfire project) and traces appear at https://logfire.pydantic.dev.

Call ``configure_observability()`` once at startup, after .env is loaded.
"""

from __future__ import annotations

import logfire

_configured = False


def configure_observability() -> None:
    """Configure Logfire + pydantic-ai instrumentation. Idempotent and safe without a token."""
    global _configured
    if _configured:
        return
    _configured = True

    # if-token-present: no LOGFIRE_TOKEN -> silent no-op; token set -> ships traces.
    logfire.configure(
        send_to_logfire="if-token-present",
        service_name="sports-fan-concierge",
        console=False,  # don't spam the uvicorn console; the AgentTrace UI is the live view.
    )
    # Patches pydantic-ai's Agent globally -> coordinator + all sub-agents become spans.
    logfire.instrument_pydantic_ai()

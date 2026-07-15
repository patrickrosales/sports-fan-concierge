"""Local Experience Agent -- nearby dining + transit tips.

This is the "live" slice of the hybrid data design: it uses Claude's built-in
web_search tool to find current nearby options, rather than seed data.
"""

from __future__ import annotations

from pydantic_ai import Agent, WebSearchTool
from pydantic_ai.capabilities import NativeTool

from ..models import LocalResult
from ..settings import MODEL

local_agent = Agent(
    MODEL,
    output_type=LocalResult,
    defer_model_check=True,
    # Live web search (Anthropic native tool) is attached via the capabilities API.
    # max_uses trimmed from 3 -> 2: this call dominates end-to-end latency (measured
    # 60-160s+ this session), and 2 searches is enough for dining + transit tips.
    capabilities=[NativeTool(WebSearchTool(max_uses=2))],
    instructions=(
        "You are the Local Experience Agent for a Toronto sports concierge. "
        "Given a venue and its neighbourhood, use web search to find a few good nearby "
        "restaurants and practical public-transit / arrival tips (prefer TTC subway, "
        "streetcar, GO Transit, or walking over driving). "
        "Keep each tip concrete and one line. Aim for 3-4 dining options and 2-3 "
        "getting-there tips. If search returns little, give sensible general Toronto "
        "transit guidance rather than inventing specific business names."
    ),
)

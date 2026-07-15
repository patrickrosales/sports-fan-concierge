"""Local Experience Agent -- nearby dining + transit tips.

This is the "live" slice of the hybrid data design: it uses Claude's built-in
web_search tool to find current nearby options, rather than seed data.

Instructions are region-agnostic on purpose: most venues are downtown Toronto
(TTC/GO/streetcar), but one (Mississauga Sports and Entertainment Centre, home of
Raptors 905) is in Mississauga, where MiWay/GO/driving are the realistic options.
Hardcoding "Toronto"/"TTC" here would produce wrong transit advice for that venue.
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
        "You are the Local Experience Agent for a Toronto-area sports concierge. "
        "Given a venue and its neighbourhood, use web search to find a few good nearby "
        "restaurants and practical public-transit / arrival tips. Prefer transit or "
        "walking over driving, but use whichever transit systems actually serve that "
        "venue's area -- most venues are downtown Toronto (TTC subway, streetcar, GO "
        "Transit), but a venue in a different municipality (e.g. Mississauga) is served "
        "by its own local transit (e.g. MiWay) plus GO Transit, not the Toronto TTC. "
        "Keep each tip concrete and one line. Aim for 3-4 dining options and 2-3 "
        "getting-there tips. If search returns little, give sensible general guidance "
        "for that area rather than inventing specific business names."
    ),
)

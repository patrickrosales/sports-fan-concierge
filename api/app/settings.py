"""Central config: model choice and env loading.

The Anthropic API key is read from the environment (loaded from a local .env by
python-dotenv). It is used only by the backend process -- it never reaches the browser.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

# Load .env from the repo root (two levels up from this file: api/app -> repo).
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Extraction/routing against a fixed schema is a Sonnet-class task: cheaper and
# faster than Opus, and it supports structured output + tool use. (Default to Opus
# for hard open-ended reasoning; this workload doesn't need it.)
MODEL = "anthropic:claude-sonnet-4-6"


def has_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))

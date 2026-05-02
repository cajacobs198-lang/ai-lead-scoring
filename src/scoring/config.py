import os
from dataclasses import dataclass


@dataclass
class LLMSettings:
    api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
    model: str = os.environ.get("LLM_MODEL", "claude-haiku-4-5-20251001")

import json
from typing import Optional
from .config import LLMSettings
from .rules import Signal

_PROMPT = """You are a B2B lead-scoring assistant. Given the JSON lead below,
output a single JSON object with keys: fit (0-1), intent (0-1),
fit_reason (one sentence), intent_reason (one sentence). No prose, JSON only.

LEAD:
{lead_json}
"""


def classify(lead: dict, settings: Optional[LLMSettings] = None) -> dict:
    """Call Claude for fit and intent. Returns {} if no API key configured."""
    s = settings or LLMSettings()
    if not s.api_key:
        return {}
    # Imported lazily so the package is usable without anthropic installed at
    # call sites that never invoke the LLM (e.g. rule-only scoring).
    from anthropic import Anthropic  # noqa: WPS433

    client = Anthropic(api_key=s.api_key)
    msg = client.messages.create(
        model=s.model,
        max_tokens=300,
        messages=[{"role": "user", "content": _PROMPT.format(lead_json=json.dumps(lead))}],
    )
    text = msg.content[0].text.strip()
    # Be lenient: extract first {...} blob.
    start = text.find("{")
    end = text.rfind("}")
    return json.loads(text[start:end + 1])


def llm_signals(
    lead: dict,
    fit_weight: int,
    intent_weight: int,
    classify_fn=classify,
) -> list[Signal]:
    raw = classify_fn(lead)
    if not raw:
        return []
    fit = float(raw.get("fit", 0))
    intent = float(raw.get("intent", 0))
    return [
        Signal(
            name="llm_fit",
            weight=int(round(fit * fit_weight)),
            source="llm",
            reason=raw.get("fit_reason", ""),
        ),
        Signal(
            name="intent",
            weight=int(round(intent * intent_weight)),
            source="llm",
            reason=raw.get("intent_reason", ""),
        ),
    ]

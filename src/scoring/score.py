from .rules import RuleSet, apply_rules, Signal
from .llm import llm_signals


def tier_for(score: int, tiers: dict[str, int]) -> str:
    for label in ("A", "B", "C"):
        if label in tiers and score >= tiers[label]:
            return label
    return "D"


def score_lead(
    lead: dict,
    ruleset: RuleSet,
    classify_fn=None,
) -> dict:
    signals: list[Signal] = apply_rules(lead, ruleset)
    if ruleset.llm_enabled:
        kwargs = {"classify_fn": classify_fn} if classify_fn else {}
        signals.extend(
            llm_signals(lead, ruleset.llm_fit_weight, ruleset.llm_intent_weight, **kwargs)
        )
    raw = sum(s.weight for s in signals)
    capped = max(0, min(100, raw))
    return {
        "lead": lead.get("email") or lead.get("domain"),
        "score": capped,
        "tier": tier_for(capped, ruleset.tiers),
        "signals": [s.__dict__ for s in signals],
    }

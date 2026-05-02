from scoring.rules import load_rules
from scoring.score import score_lead, tier_for


GOOD_LEAD = {
    "email": "sara@notion.so",
    "title": "Director of Revenue Operations",
    "industry": "Productivity Software",
    "employee_count": 800,
    "country": "US",
    "technologies": ["Salesforce"],
}

BAD_LEAD = {
    "email": "jake@tinybakery.com",
    "title": "Owner",
    "industry": "Food Service",
    "employee_count": 8,
    "country": "US",
    "technologies": [],
}


def _stub_llm(_lead):
    return {"fit": 0.9, "intent": 0.7, "fit_reason": "high fit", "intent_reason": "hiring SE"}


def test_good_lead_high_score(tmp_path):
    rs = load_rules("rules.yaml")
    out = score_lead(GOOD_LEAD, rs, classify_fn=_stub_llm)
    assert out["tier"] == "A"
    assert out["score"] >= 70
    assert any(s["name"] == "intent" for s in out["signals"])


def test_bad_lead_low_score():
    rs = load_rules("rules.yaml")
    rs.llm_enabled = False
    out = score_lead(BAD_LEAD, rs)
    assert out["tier"] in ("C", "D")


def test_score_capped_at_100():
    from scoring.rules import RuleSet, Signal
    from scoring import score as score_mod

    # Many positive rules should still cap at 100.
    rs = RuleSet(
        rules=[{"name": f"r{i}", "when": "True", "weight": 50, "reason": "x"} for i in range(10)],
        llm_enabled=False, llm_fit_weight=0, llm_intent_weight=0,
        tiers={"A": 70},
    )
    out = score_mod.score_lead({}, rs)
    assert out["score"] == 100


def test_tier_for():
    tiers = {"A": 70, "B": 50, "C": 30}
    assert tier_for(85, tiers) == "A"
    assert tier_for(60, tiers) == "B"
    assert tier_for(40, tiers) == "C"
    assert tier_for(10, tiers) == "D"

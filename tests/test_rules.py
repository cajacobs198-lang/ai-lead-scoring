import pytest
from scoring.rules import safe_eval, load_rules, apply_rules


def test_safe_eval_arithmetic_and_comparison():
    assert safe_eval("200 <= x <= 5000", {"x": 800}) is True
    assert safe_eval("200 <= x <= 5000", {"x": 50}) is False


def test_safe_eval_in_operator():
    assert safe_eval("industry in ['SaaS', 'Fintech']", {"industry": "SaaS"}) is True
    assert safe_eval("industry in ['SaaS']", {"industry": "Food"}) is False


def test_safe_eval_any_helper():
    assert safe_eval(
        "any(t in (title or '') for t in ['VP', 'Director'])",
        {"title": "Director of Sales"},
    ) is True


def test_safe_eval_blocks_attribute_access():
    with pytest.raises(ValueError):
        safe_eval("x.__class__", {"x": 1})


def test_load_and_apply(tmp_path):
    yaml = tmp_path / "r.yaml"
    yaml.write_text("""
rules:
  - name: small_co
    when: "employee_count < 50"
    weight: -10
    reason: "only {employee_count} employees"
llm: {enabled: false}
tiers: {A: 70, B: 50}
""")
    rs = load_rules(yaml)
    sigs = apply_rules({"employee_count": 8}, rs)
    assert len(sigs) == 1
    assert sigs[0].weight == -10
    assert "8 employees" in sigs[0].reason

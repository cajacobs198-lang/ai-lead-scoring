import ast
import operator as op
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Safe-eval: only allow a handful of operators and builtins.
_OPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.Mod: op.mod, ast.Eq: op.eq, ast.NotEq: op.ne, ast.Lt: op.lt,
    ast.LtE: op.le, ast.Gt: op.gt, ast.GtE: op.ge, ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b, ast.Not: op.not_, ast.USub: op.neg,
    ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b,
    ast.Is: op.is_, ast.IsNot: op.is_not,
}
_BUILTINS = {"any": any, "all": all, "len": len, "min": min, "max": max, "sum": sum}


def safe_eval(expr: str, lead: dict) -> Any:
    """Evaluate a rule expression with no attribute access and a fixed builtin set."""
    tree = ast.parse(expr, mode="eval")

    def walk(n):
        if isinstance(n, ast.Expression):
            return walk(n.body)
        if isinstance(n, ast.Constant):
            return n.value
        if isinstance(n, ast.Name):
            if n.id in _BUILTINS:
                return _BUILTINS[n.id]
            return lead.get(n.id)
        if isinstance(n, ast.BoolOp):
            vals = [walk(v) for v in n.values]
            if isinstance(n.op, ast.And):
                out = True
                for v in vals:
                    out = out and v
                return out
            out = False
            for v in vals:
                out = out or v
            return out
        if isinstance(n, ast.UnaryOp):
            return _OPS[type(n.op)](walk(n.operand))
        if isinstance(n, ast.BinOp):
            return _OPS[type(n.op)](walk(n.left), walk(n.right))
        if isinstance(n, ast.Compare):
            left = walk(n.left)
            for opn, right_node in zip(n.ops, n.comparators):
                right = walk(right_node)
                if not _OPS[type(opn)](left, right):
                    return False
                left = right
            return True
        if isinstance(n, ast.List):
            return [walk(e) for e in n.elts]
        if isinstance(n, ast.Tuple):
            return tuple(walk(e) for e in n.elts)
        if isinstance(n, ast.Set):
            return {walk(e) for e in n.elts}
        if isinstance(n, ast.Subscript):
            return walk(n.value)[walk(n.slice)]
        if isinstance(n, ast.GeneratorExp):
            # only support single-source comprehensions
            return (walk(n.elt) for _ in walk(n.generators[0].iter))
        if isinstance(n, ast.Call):
            f = walk(n.func)
            args = [walk(a) for a in n.args]
            return f(*args)
        raise ValueError(f"unsupported node {type(n).__name__}")

    return walk(tree)


@dataclass
class Signal:
    name: str
    weight: int
    source: str  # 'rule' | 'llm'
    reason: str


@dataclass
class RuleSet:
    rules: list[dict]
    llm_enabled: bool
    llm_fit_weight: int
    llm_intent_weight: int
    tiers: dict[str, int]


def load_rules(path: str | Path) -> RuleSet:
    raw = yaml.safe_load(Path(path).read_text())
    llm = raw.get("llm", {})
    return RuleSet(
        rules=raw.get("rules", []),
        llm_enabled=bool(llm.get("enabled", False)),
        llm_fit_weight=int(llm.get("fit_weight", 0)),
        llm_intent_weight=int(llm.get("intent_weight", 0)),
        tiers=raw.get("tiers", {"A": 70, "B": 50, "C": 30}),
    )


def apply_rules(lead: dict, ruleset: RuleSet) -> list[Signal]:
    out: list[Signal] = []
    for r in ruleset.rules:
        try:
            fired = bool(safe_eval(r["when"], lead))
        except Exception:
            fired = False
        if fired:
            try:
                reason = r["reason"].format(**lead)
            except Exception:
                reason = r["reason"]
            out.append(Signal(name=r["name"], weight=int(r["weight"]), source="rule", reason=reason))
    return out

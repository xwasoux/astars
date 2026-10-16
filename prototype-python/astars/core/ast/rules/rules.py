from typing import Dict, Iterable
from .base import Rule


class RuleRegistry:
    def __init__(self, rules: Iterable[Rule]):
        self._rules: Dict[str, Rule] = {}
        for rule in rules:
            if rule.cst in self._rules:
                raise ValueError(f"Duplicate rule for cst type: {rule.cst!r}")
            self._rules[rule.cst] = rule

    def get(self, cst_type: str) -> Rule | None:
        return self._rules.get(cst_type)

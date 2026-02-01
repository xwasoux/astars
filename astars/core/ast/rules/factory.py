from __future__ import annotations

from .rules import RuleRegistry
from .python import PYTHON_RULES


def build_registry(lang: str) -> RuleRegistry:
    if lang == "python":
        return RuleRegistry(PYTHON_RULES)
    raise ValueError(f"unsupported lang: {lang}")

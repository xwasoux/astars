from __future__ import annotations

from .rules import RuleRegistry
from .python import PYTHON_RULES


def build_python_registry() -> RuleRegistry:
    return RuleRegistry(PYTHON_RULES)

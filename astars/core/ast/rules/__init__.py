from .base import Rule, ChildRule
from .python import PYTHON_RULES

ALL_RULES = [
    *PYTHON_RULES,
]

__all__ = [
    "ALL_RULES",
    "PYTHON_RULES",
]

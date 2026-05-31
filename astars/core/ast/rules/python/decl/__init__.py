from .variable import PY_VARIABLE_RULES
from .function import PY_FUNCTION_RULES
from .class_ import PY_CLASS_RULES

PY_DECL_RULES = (
    *PY_VARIABLE_RULES,
    *PY_FUNCTION_RULES,
    *PY_CLASS_RULES,
)

__all__ = [
    "PY_DECL_RULES",
]

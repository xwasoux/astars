# core/ast/rules/python/__init__.py

from .misc import PY_MISC_RULES as MISC_RULES
from .literal import PY_LITERAL_RULES as LITERAL_RULES
from .control import PY_CONTROL_RULES as CONTROL_RULES
from .expr import PY_EXPR_RULES as EXPR_RULES
from .decl import PY_DECL_RULES as DECL_RULES

PYTHON_RULES = (
    *MISC_RULES,
    *LITERAL_RULES,
    *CONTROL_RULES,
    *EXPR_RULES,
    *DECL_RULES
)

__all__ = [
    "PYTHON_RULES",
]

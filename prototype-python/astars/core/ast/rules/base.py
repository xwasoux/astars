from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class ChildRule:
    """
    - name: attribute name on ASTNode (and also role in mapping if you want)
    - source: Raw child selector: field_name or "children"
    - many: whether multiple nodes should be collected
    - literal: whether to take raw.text instead of building AST
    """
    name: str
    source: str
    many: bool = False
    literal: bool = False


@dataclass(frozen=True)
class Rule:
    """
    cst: RawSyntaxNode.type
    ast: ASTNode.kind
    passthrough: if set, forward to the selected child (source)
    children: list[ChildRule]
    """
    cst: str
    ast: str
    passthrough: Optional[str] = None
    children: List[ChildRule] = None

    def __post_init__(self):
        if self.children is None:
            object.__setattr__(self, "children", [])

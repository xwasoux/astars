from __future__ import annotations

import uuid
import anytree
from typing import Any, Optional


class ASTNode(anytree.NodeMixin):
    """
    Meaning-based AST node (parser-independent).

    stable_id: deterministic identifier (recommended as external key)
    uid: uuid for debugging / internal traces
    """

    def __init__(
        self,
        *,
        kind: str,
        stable_id: str,
        parent: Optional["ASTNode"] = None,
        role: Optional[str] = None,
        value: Optional[Any] = None,
        is_async: bool = False,
    ):
        super().__init__()
        self.parent = parent

        self.kind = kind
        self.role = role
        self.value = value
        self.is_async = is_async

        self.stable_id = stable_id
        self.uid = str(uuid.uuid4())

    def __repr__(self) -> str:
        label = f"{self.kind}"
        if self.role:
            label += f"[{self.role}]"
        if getattr(self, "is_async", False):
            label += " (async)"
        if self.value is not None:
            label += f"={self.value!r}"
        return label

    def __str__(self) -> str:
        return f"ASTNode({self.kind}, id={self.stable_id}, role={self.role}, value={self.value!r})"

    def get_id(self) -> str:
        return self.stable_id

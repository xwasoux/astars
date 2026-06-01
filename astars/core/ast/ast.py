from __future__ import annotations

from dataclasses import dataclass
from anytree import RenderTree


@dataclass(frozen=True)
class AST:
    root: object

    def __str__(self) -> str:
        return "\n".join([prefix + str(node) for prefix, _, node in RenderTree(self.root)])

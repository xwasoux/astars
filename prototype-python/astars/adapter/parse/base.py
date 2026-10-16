from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import tree_sitter

from astars.core.ast.node import ASTNode
from astars.core.syntax.mapping import SyntaxGraph


Lang = Literal["python"]


class ParseError(RuntimeError):
    pass


@dataclass(frozen=True)
class ParseResult:
    """
    Parse adapter output.

    - source_bytes: original bytes parsed by tree-sitter
    - ast: AST root
    - graph: SyntaxGraph mapping (AST <-> raw spans)
    - ts_tree: raw tree-sitter tree (debug / advanced usage)
    """
    lang: str
    source_bytes: bytes
    ast: ASTNode
    graph: SyntaxGraph
    ts_tree: tree_sitter.Tree

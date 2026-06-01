from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from astars.core.syntax.mapping import SyntaxGraph
from astars.core.syntax.raw import RawSyntaxNode
from .ast import AST
from .builder import ASTBuilder
from .rules.rules import RuleRegistry


@dataclass(frozen=True)
class ASTBuildResult:
    ast: AST
    graph: SyntaxGraph


class ASTFactory:
    @staticmethod
    def create_ast(
        raw_root: RawSyntaxNode,
        registry: RuleRegistry,
        graph: Optional[SyntaxGraph] = None,
    ) -> ASTBuildResult:
        builder = ASTBuilder(registry=registry, graph=graph)
        root = builder.build(raw_root)
        return ASTBuildResult(ast=AST(root=root), graph=builder.graph)

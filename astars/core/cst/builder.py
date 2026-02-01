from astars.core.common.node_id import UnstableNodeID
from astars.core.common.stable_id import generate_stable_id
from .node import CSTNode
from .cst import CST
from ..syntax.raw import RawSyntaxNode


class CSTBuilder:
    """
    Build CST from parser-independent RawSyntaxNode.
    """

    @staticmethod
    def build(raw_root: RawSyntaxNode, lang: str) -> CST:
        root = CSTBuilder._build_node(raw_root, parent=None)
        return CST(root=root, lang=lang)

    @staticmethod
    def _build_node(raw: RawSyntaxNode, parent: CSTNode | None) -> CSTNode:
        unstable_id = UnstableNodeID.new()

        parent_stable_id = parent.stable_id if parent else None
        stable_id = generate_stable_id(
            type=raw.type,
            start=raw.start_byte,
            end=raw.end_byte,
            parent_id=parent_stable_id,
        )

        node = CSTNode(
            name=f'{raw.type}_{raw.start_byte}',
            parent=parent,
            grammar_id=raw.grammar_id,
            grammar_name=raw.grammar_name,
            start_byte=raw.start_byte,
            end_byte=raw.end_byte,
            byte_range=raw.byte_range,
            type=raw.type,
            unstable_id=unstable_id,
            stable_id=stable_id,
        )

        for ch in raw.children:
            CSTBuilder._build_node(ch.node, node)

        return node

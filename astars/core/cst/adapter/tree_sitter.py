# astars/core/cst/adapter/tree_sitter.py
import tree_sitter
from ...syntax.raw import RawSyntaxNode, RawChild

class TreeSitterAdapter:
    @staticmethod
    def to_raw(tstree: tree_sitter.Tree, source_bytes: bytes | None = None) -> RawSyntaxNode:
        return TreeSitterAdapter._convert_node(tstree.root_node, source_bytes)

    @staticmethod
    def _child_field_name(tsnode: tree_sitter.Node, index: int) -> str | None:
        # 0.25系は field_name_for_child があることが多い
        fn = getattr(tsnode, "field_name_for_child", None)
        if callable(fn):
            return fn(index)

        # フォールバック：child_by_field_name を逆探索
        # -> field 名一覧が取れない環境向け。必要ならここを拡張。
        return None

    @staticmethod
    def _node_text(tsnode: tree_sitter.Node, source_bytes: bytes | None) -> str | None:
        if source_bytes is None:
            return None
        # text は必要なら leaf のみ入れる、などポリシーをここで制御できる
        return source_bytes[tsnode.start_byte:tsnode.end_byte].decode("utf-8", errors="replace")

    @staticmethod
    def _convert_node(tsnode: tree_sitter.Node, source_bytes: bytes | None) -> RawSyntaxNode:
        children = []
        for i, child in enumerate(tsnode.children):
            field_name = TreeSitterAdapter._child_field_name(tsnode, i)
            children.append(
                RawChild(
                    field_name=field_name,
                    node=TreeSitterAdapter._convert_node(child, source_bytes),
                )
            )

        is_async = any(child.type == "async" for child in tsnode.children)

        return RawSyntaxNode(
            children=children,
            origin_id=tsnode.id,               # “同一parse内のキー”
            grammar_id=tsnode.grammar_id,
            grammar_name=tsnode.grammar_name,
            start_byte=tsnode.start_byte,
            start_point=(tsnode.start_point.row, tsnode.start_point.column),
            end_byte=tsnode.end_byte,
            end_point=(tsnode.end_point.row, tsnode.end_point.column),
            is_named=tsnode.is_named,
            is_missing=tsnode.is_missing,
            is_error=tsnode.is_error,
            is_extra=tsnode.is_extra,
            is_async=is_async,
            kind_id=tsnode.kind_id,
            type=tsnode.type,
            text=TreeSitterAdapter._node_text(tsnode, source_bytes),
        )

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union

from astars.core.common.stable_id import generate_stable_id
from astars.core.syntax.mapping import SyntaxGraph
from astars.core.syntax.raw import RawSyntaxNode
from astars.core.ast.node import ASTNode
from astars.core.ast.rules.base import ChildRule
from astars.core.ast.rules.rules import RuleRegistry


AstBuildResult = Union[ASTNode, List[ASTNode], None]
ASYNC_CAPABLE_AST = {"FunctionDef", "ForStatement", "WithStatement"}


class ASTBuilder:
    """
    Build AST from RawSyntaxNode, recording AST<->Raw mapping in SyntaxGraph.

    Important behavior:
    - ChildRule results that are ASTNode(s) are ALSO attached as anytree children
      (parent is set), so RenderTree shows them.
    - The same values are stored as attributes on the parent (test/body/...)
    """

    def __init__(self, registry: RuleRegistry, graph: Optional[SyntaxGraph] = None):
        self.registry = registry
        self.graph = graph or SyntaxGraph()
        self._raw_spans: Dict[int, Tuple[int, int]] = {}
        self._raw_index: Dict[int, RawSyntaxNode] = {}

    def build(self, raw_root: RawSyntaxNode) -> ASTNode:
        self._raw_spans, self._raw_index = self._index_raw(raw_root)

        result = self._walk(raw_root, parent=None, role=None)

        if isinstance(result, ASTNode):
            ast_root = result
        else:
            ast_root = self._new_ast_node(
                kind="Program",
                parent=None,
                role=None,
                raw_ids=[raw_root.origin_id]
            )
            if isinstance(result, list):
                for n in result:
                    n.parent = ast_root

        self.graph.index_raw_spans(self._raw_spans)

        return ast_root

    def _index_raw(self, raw_root: RawSyntaxNode) -> Tuple[Dict[int, Tuple[int, int]], Dict[int, RawSyntaxNode]]:
        spans: Dict[int, Tuple[int, int]] = {}
        index: Dict[int, RawSyntaxNode] = {}
        stack = [raw_root]
        while stack:
            n = stack.pop()
            spans[n.origin_id] = (n.start_byte, n.end_byte)
            index[n.origin_id] = n
            for ch in n.children:
                stack.append(ch.node)
        return spans, index

    # ---------------- walk ----------------

    def _walk(
        self,
        raw_node: RawSyntaxNode,
        parent: Optional[ASTNode],
        role: Optional[str],
    ) -> AstBuildResult:
        if getattr(raw_node, "is_extra", False):
            return None

        rule = self.registry.get(raw_node.type)

        if rule is None:
            return self._default_walk(raw_node, parent)

        if rule.passthrough:
            child = self._get_child(raw_node, rule.passthrough)
            if child is None:
                return None
            return self._walk(child, parent=parent, role=role)

        ast = self._new_ast_node(
            kind=rule.ast,
            parent=parent,
            role=role,
            raw_ids=[raw_node.origin_id],
        )

        for cr in rule.children:
            value = self._build_child(raw_node, ast, cr)
            setattr(ast, cr.name, value)

        if ast.kind == "StringLiteral":
            v = getattr(ast, "value", None)
            if isinstance(v, list):
                parts = []
                for x in v:
                    if isinstance(x, str):
                        parts.append(x)
                ast.value = "".join(parts)

        return ast

    def _default_walk(self, raw_node: RawSyntaxNode, parent: Optional[ASTNode]) -> AstBuildResult:
        children = [ch.node for ch in raw_node.children if not getattr(ch.node, "is_extra", False)]

        if len(children) == 1:
            return self._walk(children[0], parent=parent, role=None)

        out: List[ASTNode] = []
        for c in children:
            r = self._walk(c, parent=parent, role=None)
            if r is None:
                continue
            if isinstance(r, list):
                out.extend([x for x in r if isinstance(x, ASTNode)])
            else:
                out.append(r)

        return out if out else None

    # ---------------- child selection ----------------

    def _get_children(self, raw_node: RawSyntaxNode, source: str) -> List[RawSyntaxNode]:
        if source == "children":
            return [ch.node for ch in raw_node.children]

        if source.startswith("field:"):
            field = source[len("field:") :]
            return [ch.node for ch in raw_node.children if ch.field_name == field]

        if source.startswith("type:"):
            t = source[len("type:") :]
            return [ch.node for ch in raw_node.children if ch.node.type == t]

        if source.startswith("type_in:"):
            ts = {x.strip() for x in source[len("type_in:") :].split(",")}
            return [ch.node for ch in raw_node.children if ch.node.type in ts]

        # backward compat
        return [ch.node for ch in raw_node.children if ch.field_name == source]

    def _get_child(self, raw_node: RawSyntaxNode, source: str) -> Optional[RawSyntaxNode]:
        xs = self._get_children(raw_node, source)
        return xs[0] if xs else None

    # ---------------- build child (and attach to tree) ----------------

    def _attach_value_as_children(self, parent: ASTNode, role: str, value):
        """
        If value contains ASTNode(s), attach them under `parent` in the anytree structure.
        Also set their .role to the field name (if not already set).
        """
        if isinstance(value, ASTNode):
            if value.role is None:
                value.role = role
            value.parent = parent
            return

        if isinstance(value, list):
            for v in value:
                if isinstance(v, ASTNode):
                    if v.role is None:
                        v.role = role
                    v.parent = parent

    def _build_child(self, raw_node: RawSyntaxNode, ast_parent: ASTNode, cr: ChildRule):
        # many => list
        if cr.many:
            raws = self._get_children(raw_node, cr.source)
            items = []
            raw_ids: List[int] = []

            for rn in raws:
                raw_ids.append(rn.origin_id)

                if cr.literal:
                    items.append(getattr(rn, "text", None))
                    continue

                built = self._walk(rn, parent=None, role=cr.name)  # build detached
                if built is None:
                    continue
                if isinstance(built, list):
                    items.extend(built)
                else:
                    items.append(built)

            # mapping: parent field role uses these raw ids
            self.graph.link_ast_raw(ast_parent.stable_id, raw_ids, role=cr.name)

            # attach AST children to tree
            self._attach_value_as_children(ast_parent, cr.name, items)

            return items

        # single
        child = self._get_child(raw_node, cr.source)
        if child is None:
            return None

        self.graph.link_ast_raw(ast_parent.stable_id, [child.origin_id], role=cr.name)

        if cr.literal:
            return getattr(child, "text", None)

        built = self._walk(child, parent=None, role=cr.name)  # build detached
        if built is None:
            return None

        # attach to tree
        self._attach_value_as_children(ast_parent, cr.name, built)

        return built

    # ---------------- stable id + node creation ----------------

    def _new_ast_node(
        self,
        *,
        kind: str,
        parent: Optional[ASTNode],
        role: Optional[str],
        raw_ids: List[int],
    ) -> ASTNode:
        starts = []
        ends = []
        for rid in raw_ids:
            sp = self._raw_spans.get(rid)
            if sp is None:
                continue
            s, e = sp
            starts.append(s)
            ends.append(e)

        if not starts or not ends:
            s, e = (0, 0)
        else:
            s, e = (min(starts), max(ends))

        stable_id = generate_stable_id(
            type=kind,
            start=s,
            end=e,
            parent_id=parent.stable_id if parent else None,
        )

        node = ASTNode(kind=kind, stable_id=stable_id, parent=parent, role=role)

        if kind in ASYNC_CAPABLE_AST:
            # raw_ids は複数来ることがあるので、どれか1つでも is_async なら True
            node.is_async = any(
                getattr(self._raw_index.get(rid), "is_async", False)
                for rid in raw_ids
            )
        else:
            node.is_async = False

        self.graph.link_ast_raw(node.stable_id, raw_ids, role=role)

        return node

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

from anytree import PreOrderIter

from .mapping import SyntaxGraph, ByteSpan, AstID


@dataclass(frozen=True)
class SpanHit:
    """
    A query hit for an AST node.
    """
    node: object                 # ASTNode (kept as object to avoid import cycles)
    ast_id: AstID
    span: ByteSpan
    role: Optional[str] = None   # role constraint used (if any)


# ----------------------------
# Helpers
# ----------------------------

def _iter_ast_nodes(ast_root: object) -> Iterator[object]:
    """
    Iterate AST nodes in pre-order. Assumes anytree NodeMixin.
    """
    yield from PreOrderIter(ast_root)


def _get_ast_id(node: object) -> str:
    """
    Extract stable id from an AST node.
    """
    # You used .stable_id in your ASTNode
    return getattr(node, "stable_id")


def _span_len(span: ByteSpan) -> int:
    s, e = span
    return e - s


def _covers(span: ByteSpan, target: ByteSpan) -> bool:
    """
    Whether span fully covers target.
    """
    s, e = span
    ts, te = target
    return s <= ts and te <= e


def _overlap_len(a: ByteSpan, b: ByteSpan) -> int:
    """
    Length of overlap (0 if none).
    """
    s1, e1 = a
    s2, e2 = b
    s = max(s1, s2)
    e = min(e1, e2)
    return max(0, e - s)


# ----------------------------
# Core queries
# ----------------------------

def find_ast_nodes_covering_span(
    ast_root: object,
    graph: SyntaxGraph,
    target_span: ByteSpan,
    *,
    role: Optional[str] = None,
    predicate: Optional[Callable[[object], bool]] = None,
    limit: Optional[int] = None,
) -> List[SpanHit]:
    """
    Return AST nodes whose mapped span fully covers `target_span`.

    Ranking:
    - smaller covering span first (more specific)
    - then by traversal order (stable-ish)

    Params
    ------
    role:
        If set, uses mapping only for that role (e.g. "test", "body").
    predicate:
        Optional filter on node (e.g. only IfStatement nodes).
    limit:
        If set, returns at most `limit` hits.
    """
    hits: List[SpanHit] = []

    for node in _iter_ast_nodes(ast_root):
        if predicate is not None and not predicate(node):
            continue

        ast_id = _get_ast_id(node)
        sp = graph.span_of_ast(ast_id, role=role)
        if sp is None:
            continue

        if _covers(sp, target_span):
            hits.append(SpanHit(node=node, ast_id=ast_id, span=sp, role=role))

    hits.sort(key=lambda h: (_span_len(h.span), h.span[0], h.span[1]))

    if limit is not None:
        return hits[:limit]
    return hits


def find_best_ast_node_at_offset(
    ast_root: object,
    graph: SyntaxGraph,
    offset: int,
    *,
    role: Optional[str] = None,
    predicate: Optional[Callable[[object], bool]] = None,
) -> Optional[SpanHit]:
    """
    Convenience: treat offset as a 0-length span (offset, offset),
    and return the most specific AST node that covers it.
    """
    hits = find_ast_nodes_covering_span(
        ast_root,
        graph,
        (offset, offset),
        role=role,
        predicate=predicate,
        limit=1,
    )
    return hits[0] if hits else None


def find_ast_nodes_overlapping_span(
    ast_root: object,
    graph: SyntaxGraph,
    target_span: ByteSpan,
    *,
    role: Optional[str] = None,
    predicate: Optional[Callable[[object], bool]] = None,
    min_overlap: int = 1,
    limit: Optional[int] = None,
) -> List[SpanHit]:
    """
    Return AST nodes whose mapped span overlaps `target_span`.

    Ranking:
    - larger overlap first
    - then smaller node span (more specific)

    Useful when users drag-select a region and you want candidates.
    """
    hits: List[SpanHit] = []

    for node in _iter_ast_nodes(ast_root):
        if predicate is not None and not predicate(node):
            continue

        ast_id = _get_ast_id(node)
        sp = graph.span_of_ast(ast_id, role=role)
        if sp is None:
            continue

        ol = _overlap_len(sp, target_span)
        if ol >= min_overlap:
            hits.append(SpanHit(node=node, ast_id=ast_id, span=sp, role=role))

    hits.sort(key=lambda h: (-_overlap_len(h.span, target_span), _span_len(h.span), h.span[0]))

    if limit is not None:
        return hits[:limit]
    return hits


def resolve_ast_ids_to_nodes(
    ast_root: object,
    ast_ids: Iterable[str],
) -> List[object]:
    """
    Given stable IDs, return node objects found under ast_root.
    """
    wanted = set(ast_ids)
    out: List[object] = []
    for node in _iter_ast_nodes(ast_root):
        nid = _get_ast_id(node)
        if nid in wanted:
            out.append(node)
    return out


def find_ast_nodes_linked_to_raw(
    ast_root: object,
    graph: SyntaxGraph,
    raw_origin_id: int,
) -> List[object]:
    """
    Reverse lookup:
      raw origin_id -> [ASTNode objects]

    Uses graph.asts_of_raw(...) then resolves to node objects.
    """
    ast_ids = graph.asts_of_raw(raw_origin_id)
    return resolve_ast_ids_to_nodes(ast_root, ast_ids)


def collect_ast_spans(
    ast_root: object,
    graph: SyntaxGraph,
    *,
    role: Optional[str] = None,
    predicate: Optional[Callable[[object], bool]] = None,
) -> List[SpanHit]:
    """
    Collect spans for all nodes (optionally role-filtered).
    This is handy to precompute for UI rendering or building an index.
    """
    hits: List[SpanHit] = []
    for node in _iter_ast_nodes(ast_root):
        if predicate is not None and not predicate(node):
            continue
        ast_id = _get_ast_id(node)
        sp = graph.span_of_ast(ast_id, role=role)
        if sp is None:
            continue
        hits.append(SpanHit(node=node, ast_id=ast_id, span=sp, role=role))
    return hits

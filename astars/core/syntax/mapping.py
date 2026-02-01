from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple


AstID = str
RawOriginID = int
ByteSpan = Tuple[int, int]
Role = Optional[str]


@dataclass(frozen=True)
class Link:
    """
    One mapping edge from an AST node to 1..N raw origin nodes.
    role is optional (e.g. "test", "body", "iter").
    """
    ast_id: AstID
    raw_ids: Tuple[RawOriginID, ...]
    role: Role = None


@dataclass
class SyntaxGraph:
    """
    Many-to-many mapping between AST nodes and RawSyntax nodes (by IDs only).

    Stores:
    - ast_id -> links (with optional role)
    - raw_origin_id -> ast_id set (reverse index)
    - raw_origin_id -> (start_byte, end_byte) (span index)

    With this, you can answer:
    - which raw nodes correspond to an AST node?
    - which AST nodes correspond to a raw node?
    - what source span covers an AST node (optionally by role)?
    """

    _ast_to_links: Dict[AstID, List[Link]] = field(default_factory=dict)
    _raw_to_asts: Dict[RawOriginID, Set[AstID]] = field(default_factory=dict)
    _raw_spans: Dict[RawOriginID, ByteSpan] = field(default_factory=dict)

    # ----------------------------
    # Indexing raw spans
    # ----------------------------

    def index_raw_span(self, raw_origin_id: RawOriginID, start_byte: int, end_byte: int) -> None:
        self._raw_spans[raw_origin_id] = (start_byte, end_byte)

    def index_raw_spans(self, raw_spans: Dict[RawOriginID, ByteSpan]) -> None:
        """
        Bulk load spans, typically from ASTBuilder's raw traversal index.
        """
        self._raw_spans.update(raw_spans)

    # ----------------------------
    # Linking
    # ----------------------------

    def link_ast_raw(
        self,
        ast_id: AstID,
        raw_origin_ids: Iterable[RawOriginID],
        role: Role = None,
    ) -> None:
        raw_ids = tuple(raw_origin_ids)
        if not raw_ids:
            return

        link = Link(ast_id=ast_id, raw_ids=raw_ids, role=role)
        self._ast_to_links.setdefault(ast_id, []).append(link)

        for rid in raw_ids:
            self._raw_to_asts.setdefault(rid, set()).add(ast_id)

    # ----------------------------
    # Queries: ID level
    # ----------------------------

    def raw_of_ast(self, ast_id: AstID, role: Role = None) -> List[RawOriginID]:
        """
        Return raw origin IDs mapped to an AST node.
        If role is given, filters links by role.
        """
        links = self._ast_to_links.get(ast_id, [])
        out: List[RawOriginID] = []
        for lk in links:
            if role is not None and lk.role != role:
                continue
            out.extend(lk.raw_ids)
        return out

    def asts_of_raw(self, raw_origin_id: RawOriginID) -> List[AstID]:
        """
        Reverse lookup: which AST node IDs refer to this raw node?
        """
        return sorted(self._raw_to_asts.get(raw_origin_id, set()))

    def roles_of_ast(self, ast_id: AstID) -> List[str]:
        """
        What roles have been recorded for this AST node?
        """
        roles: List[str] = []
        for lk in self._ast_to_links.get(ast_id, []):
            if lk.role is not None:
                roles.append(lk.role)
        return roles

    # ----------------------------
    # Queries: span level
    # ----------------------------

    def span_of_raw(self, raw_origin_id: RawOriginID) -> Optional[ByteSpan]:
        return self._raw_spans.get(raw_origin_id)

    def span_of_ast(self, ast_id: AstID, role: Role = None) -> Optional[ByteSpan]:
        """
        Compute the covering span for an AST node from mapped raw nodes.
        If role is given, use only the raw nodes linked with that role.
        """
        raw_ids = self.raw_of_ast(ast_id, role=role)
        if not raw_ids:
            return None

        starts: List[int] = []
        ends: List[int] = []
        for rid in raw_ids:
            sp = self._raw_spans.get(rid)
            if sp is None:
                continue
            s, e = sp
            starts.append(s)
            ends.append(e)

        if not starts or not ends:
            return None
        return (min(starts), max(ends))

    def slice_of_ast(
        self,
        ast_id: AstID,
        source_bytes: bytes,
        role: Role = None,
    ) -> Optional[bytes]:
        """
        Convenience: returns the byte slice corresponding to span_of_ast.
        """
        sp = self.span_of_ast(ast_id, role=role)
        if sp is None:
            return None
        s, e = sp
        return source_bytes[s:e]

        # ----------------------------
    # Queries: pos -> raw/ast
    # ----------------------------

    def raws_covering(self, pos: int) -> List[RawOriginID]:
        """
        Return raw IDs whose span covers the given byte position.
        Sorted by increasing span length (smallest/most specific first).
        """
        hits: List[Tuple[int, RawOriginID]] = []
        for rid, (s, e) in self._raw_spans.items():
            if s <= pos < e:
                hits.append((e - s, rid))
        hits.sort(key=lambda x: x[0])
        return [rid for _, rid in hits]

    def raw_at(self, pos: int) -> Optional[RawOriginID]:
        """
        Return the most specific raw node covering pos (smallest span).
        """
        xs = self.raws_covering(pos)
        return xs[0] if xs else None

    def asts_covering(self, pos: int, role: Role = None) -> List[AstID]:
        """
        Return AST IDs whose computed span covers pos.
        Sorted by increasing span length (smallest/most specific first).
        """
        hits: List[Tuple[int, AstID]] = []
        for ast_id in self._ast_to_links.keys():
            sp = self.span_of_ast(ast_id, role=role)
            if sp is None:
                continue
            s, e = sp
            if s <= pos < e:
                hits.append((e - s, ast_id))
        hits.sort(key=lambda x: x[0])
        return [ast_id for _, ast_id in hits]

    def ast_at(self, pos: int, role: Role = None) -> Optional[AstID]:
        """
        Return the most specific AST node covering pos.

        Strategy:
        1) Find most specific raw node covering pos.
        2) From ASTs linked to that raw node, pick the most specific AST (smallest span).
        Fallback: compute over all AST spans if reverse index yields nothing.
        """
        rid = self.raw_at(pos)
        if rid is not None:
            candidates = self.asts_of_raw(rid)
            best_id: Optional[AstID] = None
            best_len: Optional[int] = None

            for ast_id in candidates:
                sp = self.span_of_ast(ast_id, role=role)
                if sp is None:
                    continue
                s, e = sp
                if not (s <= pos < e):
                    continue
                ln = e - s
                if best_len is None or ln < best_len:
                    best_len = ln
                    best_id = ast_id

            if best_id is not None:
                return best_id

        # fallback: slower but robust
        xs = self.asts_covering(pos, role=role)
        return xs[0] if xs else None


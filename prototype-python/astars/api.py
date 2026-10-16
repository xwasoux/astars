from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional

from astars.text import SourceText

if TYPE_CHECKING:
    from astars.core.ast.node import ASTNode


class AstarsError(RuntimeError):
    """Base exception for public Astars API errors."""


class UnsupportedLanguageError(AstarsError):
    """Raised when a language is not supported by the public API."""


class ParserUnavailableError(AstarsError):
    """Raised when a parser dependency required for a language is unavailable."""


@dataclass(frozen=True)
class SourceSpan:
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    message: str
    span: Optional[SourceSpan] = None


@dataclass(frozen=True)
class SourceUnit:
    lang: str
    path: Optional[Path]
    source: str
    root: "ASTNode"
    diagnostics: tuple[Diagnostic, ...]
    _source_text: SourceText
    _graph: object

    def walk(self, kind: Optional[str] = None) -> Iterator["ASTNode"]:
        for node in _walk_preorder(self.root):
            if kind is None or getattr(node, "kind", None) == kind:
                yield node

    def find(self, kind: Optional[str] = None) -> list["ASTNode"]:
        return list(self.walk(kind=kind))

    def node_at(self, byte_offset: int) -> Optional["ASTNode"]:
        self._validate_byte_offset(byte_offset)
        if self._source_text.is_eof(byte_offset):
            return None

        ast_id = self._graph.ast_at(byte_offset)
        if ast_id is None:
            return None

        for node in self.walk():
            if _node_id(node) == ast_id:
                return node
        return None

    def span_of(self, node: "ASTNode") -> Optional[SourceSpan]:
        self._ensure_owns_node(node)

        span = self._graph.span_of_ast(_node_id(node))
        if span is None:
            return None

        start_byte, end_byte = span
        return self._source_span_from_range(start_byte, end_byte)

    def source_of(self, node: "ASTNode") -> Optional[str]:
        span = self.span_of(node)
        if span is None:
            return None
        return self._source_text.slice_text(span.start_byte, span.end_byte)

    def _validate_byte_offset(self, byte_offset: int) -> None:
        try:
            self._source_text.validate_offset(byte_offset)
        except ValueError as exc:
            raise AstarsError(str(exc)) from exc

    def _ensure_owns_node(self, node: "ASTNode") -> None:
        if not any(candidate is node for candidate in self.walk()):
            raise AstarsError("node does not belong to this SourceUnit")

    def _source_span_from_range(self, start_byte: int, end_byte: int) -> SourceSpan:
        try:
            self._source_text.validate_range(start_byte, end_byte)
            return SourceSpan(
                start_byte=start_byte,
                end_byte=end_byte,
                start_point=self._source_text.point_at(start_byte),
                end_point=self._source_text.point_at(end_byte),
            )
        except ValueError as exc:
            raise AstarsError(str(exc)) from exc


def parse_str(source: str, *, lang: str, path: str | Path | None = None) -> SourceUnit:
    _ensure_supported_lang(lang)
    result = _call_parser(
        lambda: _adapter_parse_functions()[2](source, lang=lang)
    )
    return _to_source_unit(result, source=source, path=path)


def parse_bytes(source_bytes: bytes, *, lang: str, path: str | Path | None = None) -> SourceUnit:
    _ensure_supported_lang(lang)
    result = _call_parser(
        lambda: _adapter_parse_functions()[1](source_bytes, lang=lang)
    )
    return _to_source_unit(
        result,
        source=source_bytes.decode("utf-8", errors="replace"),
        path=path,
    )


def parse_file(path: str | Path, *, lang: str, encoding: str = "utf-8") -> SourceUnit:
    _ensure_supported_lang(lang)
    p = Path(path)
    source = p.read_text(encoding=encoding, errors="replace")
    result = _call_parser(
        lambda: _adapter_parse_functions()[0](p, lang=lang, encoding=encoding)
    )
    return _to_source_unit(result, source=source, path=p)


def _to_source_unit(result, *, source: str, path: str | Path | None) -> SourceUnit:
    source_text = SourceText(source_code=source, source_bytes=result.source_bytes)
    return SourceUnit(
        lang=result.lang,
        path=Path(path) if path is not None else None,
        source=source,
        root=result.ast,
        diagnostics=_diagnostics_from_tree(result.ts_tree, source_text),
        _source_text=source_text,
        _graph=result.graph,
    )


def _call_parser(parse):
    try:
        return parse()
    except Exception as exc:
        message = str(exc)
        if "unsupported lang" in message:
            raise UnsupportedLanguageError(message) from exc
        if "not installed" in message or "does not provide" in message:
            raise ParserUnavailableError(message) from exc
        if isinstance(exc, ImportError):
            raise ParserUnavailableError(message) from exc
        raise AstarsError(message) from exc


def _ensure_supported_lang(lang: str) -> None:
    if lang != "python":
        raise UnsupportedLanguageError(f"unsupported lang: {lang}")


def _adapter_parse_functions():
    from astars.adapter.parse import parse_bytes as adapter_parse_bytes
    from astars.adapter.parse import parse_file as adapter_parse_file
    from astars.adapter.parse import parse_str as adapter_parse_str

    return adapter_parse_file, adapter_parse_bytes, adapter_parse_str


def _walk_preorder(root) -> Iterator:
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        children = list(getattr(node, "children", ()))
        stack.extend(reversed(children))


def _node_id(node) -> str:
    if hasattr(node, "id"):
        return getattr(node, "id")
    return getattr(node, "stable_id")


def _diagnostics_from_tree(ts_tree, source_text: SourceText) -> tuple[Diagnostic, ...]:
    root = getattr(ts_tree, "root_node", None)
    if root is None or not getattr(root, "has_error", False):
        return ()

    diagnostics: list[Diagnostic] = []
    stack = [root]
    while stack:
        node = stack.pop()

        if getattr(node, "is_error", False):
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    message="syntax error",
                    span=_span_from_tree_sitter_node(node, source_text),
                )
            )
        elif getattr(node, "is_missing", False):
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    message=f"missing syntax node: {getattr(node, 'type', 'unknown')}",
                    span=_span_from_tree_sitter_node(node, source_text),
                )
            )

        children = list(getattr(node, "children", ()))
        stack.extend(reversed(children))

    return tuple(diagnostics)


def _span_from_tree_sitter_node(node, source_text: SourceText) -> SourceSpan:
    start_byte = getattr(node, "start_byte")
    end_byte = getattr(node, "end_byte")
    source_text.validate_range(start_byte, end_byte)
    return SourceSpan(
        start_byte=start_byte,
        end_byte=end_byte,
        start_point=source_text.point_at(start_byte),
        end_point=source_text.point_at(end_byte),
    )

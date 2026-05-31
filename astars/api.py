from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional

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
    _source_bytes: bytes
    _graph: object

    def walk(self, kind: Optional[str] = None) -> Iterator["ASTNode"]:
        for node in _walk_preorder(self.root):
            if kind is None or getattr(node, "kind", None) == kind:
                yield node

    def find(self, kind: Optional[str] = None) -> list["ASTNode"]:
        return list(self.walk(kind=kind))

    def node_at(self, byte_offset: int) -> Optional["ASTNode"]:
        ast_id = self._graph.ast_at(byte_offset)
        if ast_id is None:
            return None

        for node in self.walk():
            if _node_id(node) == ast_id:
                return node
        return None

    def span_of(self, node: "ASTNode") -> Optional[SourceSpan]:
        span = self._graph.span_of_ast(_node_id(node))
        if span is None:
            return None

        start_byte, end_byte = span
        return SourceSpan(
            start_byte=start_byte,
            end_byte=end_byte,
            start_point=_byte_offset_to_point(self._source_bytes, start_byte),
            end_point=_byte_offset_to_point(self._source_bytes, end_byte),
        )

    def source_of(self, node: "ASTNode") -> Optional[str]:
        span = self.span_of(node)
        if span is None:
            return None
        return self._source_bytes[span.start_byte : span.end_byte].decode(
            "utf-8",
            errors="replace",
        )


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
    return SourceUnit(
        lang=result.lang,
        path=Path(path) if path is not None else None,
        source=source,
        root=result.ast,
        diagnostics=(),
        _source_bytes=result.source_bytes,
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


def _byte_offset_to_point(source_bytes: bytes, offset: int) -> tuple[int, int]:
    safe_offset = max(0, min(offset, len(source_bytes)))
    line = 0
    line_start = 0

    for idx, byte in enumerate(source_bytes[:safe_offset]):
        if byte == 0x0A:
            line += 1
            line_start = idx + 1

    return (line, safe_offset - line_start)

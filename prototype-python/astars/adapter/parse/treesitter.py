from __future__ import annotations

from pathlib import Path
from typing import Optional

import tree_sitter

from astars.core.cst.adapter.tree_sitter import TreeSitterAdapter
from astars.core.ast.builder import ASTBuilder
from astars.core.ast.rules.factory import build_python_registry
from astars.core.syntax.mapping import SyntaxGraph

from .base import Lang, ParseError, ParseResult


# ---- tree-sitter parser cache ----
_PARSER_CACHE: dict[str, tree_sitter.Parser] = {}


def _get_parser(lang: Lang) -> tree_sitter.Parser:
    if lang in _PARSER_CACHE:
        return _PARSER_CACHE[lang]

    parser = tree_sitter.Parser()

    if lang == "python":
        try:
            import tree_sitter_python  # type: ignore
        except Exception as e:
            raise ParseError("tree_sitter_python is not installed") from e

        if hasattr(tree_sitter_python, "get_language"):
            language = tree_sitter.Language(tree_sitter_python.get_language())
        elif hasattr(tree_sitter_python, "language"):
            language = tree_sitter.Language(tree_sitter_python.language())
        else:
            raise ParseError("tree_sitter_python does not provide get_language()/language()")

        parser.language = language
    else:
        raise ParseError(f"unsupported lang: {lang}")

    _PARSER_CACHE[lang] = parser
    return parser


def parse_bytes(source_bytes: bytes, *, lang: Lang) -> ParseResult:
    ts_parser = _get_parser(lang)
    ts_tree = ts_parser.parse(source_bytes)

    raw_root = TreeSitterAdapter.to_raw(ts_tree, source_bytes)

    graph = SyntaxGraph()
    registry = build_python_registry()  # Step2: python固定でOK（Langがpythonのみだから）
    builder = ASTBuilder(registry=registry, graph=graph)
    ast_root = builder.build(raw_root)

    return ParseResult(
        lang=lang,
        source_bytes=source_bytes,
        ast=ast_root,
        graph=graph,
        ts_tree=ts_tree,
    )


def parse_str(source: str, *, lang: Lang, encoding: str = "utf-8") -> ParseResult:
    """
    Convenience for tests/REPL.
    """
    return parse_bytes(source.encode(encoding), lang=lang)


def parse_file(path: str | Path, *, lang: Lang, encoding: Optional[str] = None) -> ParseResult:
    p = Path(path)
    data = p.read_bytes()

    # 既存仕様維持：encoding 指定時は decode→utf-8 encode
    if encoding is not None:
        text = data.decode(encoding, errors="replace")
        data = text.encode("utf-8")

    return parse_bytes(data, lang=lang)

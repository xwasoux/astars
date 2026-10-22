# Changelog

## 0.2.0 - Unreleased

Astars 0.2.0 is the first release of the Rust core (`crates/astars-core`) and
its Python (`bindings/python`, module `_astars`) and Node.js
(`bindings/node`, `@astars/native`) bindings. It replaces the pure-Python
`astars` 0.1.0 implementation as the actively developed line; see
`prototype-python/README.md` for the frozen 0.1.0 reference.

### Added

- `parse_str` / `parse_bytes` / `parse_file` (with WHATWG encoding support)
- `SyntaxTree` query API: `walk`, `find(kind)`, `node_at(offset)`,
  `span_of`, `source_of`, `point_at(byte_offset)`
- Edit primitive (v1): `replace(target, new_text)` + `unchanged_in(id, edit)`
- Parser-recovery diagnostics (`ERROR`/`MISSING` nodes)
- Python and Node.js examples covering the full v0 surface

### Known Limitations

- Lineage tracking across edits and name/kind-based node addressing
  (`EDIT_MODEL.ja.md` operations 9 and 10) are not included.
- Structural diff between independently parsed trees (operation 13) is not
  included.
- No downstream `astars-*` package exists yet.

## 0.1.0 - 2026-06-01

Astars 0.1.0 is the first v0 public API release.

This release repositions Astars as a lightweight program-structure engine: it
parses Python source code, exposes an AST-like structure, supports simple
structure queries, and maps nodes back to source spans and source text.

### Added

- Top-level public parse API:
  - `astars.parse_str`
  - `astars.parse_bytes`
  - `astars.parse_file`
- Public result and support objects:
  - `astars.SourceUnit`
  - `astars.SourceSpan`
  - `astars.Diagnostic`
  - `astars.AstarsError`
  - `astars.UnsupportedLanguageError`
  - `astars.ParserUnavailableError`
- `SourceUnit` traversal, query, and source-mapping helpers:
  - `unit.walk(kind=None)`
  - `unit.find(kind=None)`
  - `unit.node_at(byte_offset)`
  - `unit.span_of(node)`
  - `unit.source_of(node)`
- Minimal parser recovery diagnostics for tree-sitter `ERROR` and `MISSING`
  nodes.
- Public API tests covering parsing, encoding, source spans, diagnostics, and
  unsupported languages.
- Python example based on the v0 public API.
- Release helper scripts for build, artifact check, and PyPI/TestPyPI upload.

### Changed

- Package metadata is now managed through `pyproject.toml`.
- Runtime dependencies are limited to `anytree`, `tree-sitter`, and
  `tree-sitter-python`.
- The package requires Python 3.10 or newer.
- README and design documents now describe Astars as an engine layer rather than
  an application-specific analysis tool.

### Removed

- Legacy `setup.py` / `setup.cfg` packaging metadata.
- Outdated Java example.
- README examples based on legacy `AParser` / `APruner` APIs.

### Known Limitations

- v0 supports Python as the reference language.
- Source editing primitives are not included.
- Stable CST and `RawSyntaxNode` public APIs are not included.
- Semantic analysis, metrics, code review, pruning, and LLM-specific policies
  belong in downstream packages.
- Legacy `AParser`, `APruner`, and `ATraverser` compatibility wrappers are not
  part of this release.

### Verification

- Public API test suite passes.
- Python example runs successfully.
- Wheel and source distribution build successfully.
- Built wheel installs into a clean environment and passes an `import astars` /
  `parse_str(..., lang="python")` smoke test.

# Changelog

## 0.1.1 - Unreleased

Astars 0.1.1 is planned as a release-process polish update for the v0.1 line.
It does not change the v0 public API.

### Added

- `checkInstall.sh` for clean install smoke tests from local wheel artifacts,
  TestPyPI, or PyPI.

### Changed

- Improved `checkPypi.sh` and `registPypi.sh` error messages when release
  dependencies such as `build` or `twine` are missing.
- Updated the release checklist to use `checkPypi.sh`, `checkInstall.sh`, and
  `registPypi.sh` as the canonical release verification flow.
- Refreshed Japanese strategy and release documents for the post-`0.1.0`
  project state.

### Verification

- Public API test suite passes.
- Local wheel clean install smoke test passes through `checkInstall.sh dist`.
- Wheel and source distribution checks pass through `checkPypi.sh`.

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

<p align="center">
  <img src="https://raw.githubusercontent.com/xwasoux/astars/main/docs/assets/logo.png" alt="Astars logo" width="520">
</p>

<h1 align="center">Astars</h1>

<p align="center">
  <strong>A lightweight program-structure engine.</strong>
</p>

Astars parses source code into an AST-like structure, lets users inspect and query
that structure, map nodes back to their original source spans and source text, and
apply a minimal source-aware edit primitive. Astars is intended to be a small
engine that downstream packages can build on, rather than a full analysis product
by itself.

## Project Status

**Astars's core engine is being rewritten in Rust** (`crates/astars-core`), with
Python and Node.js as binding-based consumers (`bindings/python`, `bindings/node`
in this repository). See [`docs/STRATEGY.ja.md`](docs/STRATEGY.ja.md) for the
rationale and [`docs/ACTION_ITEMS.ja.md`](docs/ACTION_ITEMS.ja.md) for current
status.

The Rust core has reached its v0 scope end-to-end through both bindings. It is
**not yet published to PyPI or npm** - see [Build From Source](#build-from-source)
below to try it. The previously published pure-Python implementation (`astars`
0.1.0 on PyPI) is kept as a frozen reference under
[`prototype-python/`](prototype-python/) and is no longer under active
development; see [Installing the Previous Release](#installing-the-previous-release)
if you want that version instead.

The current v0 scope (Rust core):

- parse Python source from a string, raw bytes, or a file (with encoding support)
- inspect AST-like nodes - tree-sitter's raw CST, 1:1 - without touching
  parser-specific objects directly
- walk the tree, find nodes by kind, and locate the most specific node at a byte
  offset
- map nodes to byte spans, source text, and 0-based line/column positions
- a minimal edit primitive: replace a node's source span, and ask whether another
  node survived that edit unchanged
- parser-recovery diagnostics (syntax errors)

The following are outside the v0 scope:

- insert/delete-specific edit methods, a Piece Table, edit lineage tracking, and
  name/kind-based node addressing (the planned v2 of the edit primitive)
- a selector DSL
- a stable CST / raw-node public API
- semantic analysis
- languages other than Python
- downstream packages themselves (`astars-metrics`, `astars-code-review`, etc.)

## Build From Source

Requires a recent Rust toolchain. Verify the core engine builds and tests on its
own first:

```bash
git clone https://github.com/xwasoux/astars.git
cd astars
cargo test --workspace
```

### Python binding

```bash
cd bindings/python
python3 -m venv .venv && source .venv/bin/activate
pip install maturin
maturin develop
python3 ../../examples/python/basic_parse.py
```

### Node binding

```bash
cd bindings/node
npm install
npm run build:debug
node ../../examples/node/basic-parse.js
```

Both example scripts walk through the full v0 surface (query API, the edit
primitive, `parse_bytes`/`parse_file`, diagnostics, and `point_at`) against the
same sample source, so their output lines up one-to-one.

## Quick Start

Python, via `import _astars` (the eventual `import astars` will be a thin wrapper
around this native module):

```python
import _astars

tree = _astars.parse_str("def hello(name):\n    return name\n", _astars.PyLang.Python).tree

function = tree.find("function_definition")[0]
print(tree.span_of(function))      # (0, 32)
print(tree.source_of(function))    # 'def hello(name):\n    return name'
print(tree.point_at(0))            # (0, 0)
```

Node.js, via `@astars/native`:

```js
const { parseStr, JsLang } = require('@astars/native');

const tree = parseStr('def hello(name):\n    return name\n', JsLang.Python);

const [fn] = tree.find('function_definition');
console.log(tree.spanOf(fn));   // [0, 32]
console.log(tree.sourceOf(fn)); // 'def hello(name):\n    return name'
console.log(tree.pointAt(0));   // [0, 0]
```

## Public API

The core engine (`astars-core`) exposes `Lang`, `ParseResult`, `SyntaxTree` (+
`NodeId`, `ByteSpan`, `Point`, `EditResult`, `Diagnostic`, `Severity`), and
`parse_str` / `parse_bytes` / `parse_file`. Each binding mirrors this surface in
its own idiom:

- Python (`_astars`): `PyLang`, `PyParseResult`, `PySyntaxTree`, `PyNodeInfo`,
  `PyEditResult`, `PyDiagnostic`, `parse_str` / `parse_bytes` / `parse_file`
- Node (`@astars/native`): `JsLang`, `JsSyntaxTree`, `JsNodeInfo`, `JsEditResult`,
  `JsDiagnostic`, `parseStr` / `parseBytes` / `parseFile`

For the full method-level surface of each type, see the Mermaid class diagrams in
[`docs/architecture/ARCHITECTURE.ja.md`](docs/architecture/ARCHITECTURE.ja.md)
rather than this README, so there is a single place that stays in sync with the
code.

## Design Boundary

Astars is an engine layer. It should answer questions such as:

- What is the program structure of this source file?
- Which nodes match this structural query?
- Where did this node come from in the original source?
- What source text corresponds to this node?
- What changes if I edit this node, and what else is left untouched?

Astars should not decide what a metric means, whether a code review finding is
important, or which LLM evaluation policy should be applied. Those decisions
belong in downstream packages such as `astars-metrics`, `astars-code-review`, or
`astars-llm-eval`.

## Development

Rust workspace (`crates/astars-core`, `bindings/python`, `bindings/node`):

```bash
cargo test --workspace
cargo clippy --workspace -- -D warnings
```

Rebuilding a binding after a core change:

```bash
# Python
cd bindings/python && source .venv/bin/activate && maturin develop

# Node
cd bindings/node && npm run build:debug
```

Python prototype (frozen reference, in `prototype-python/`):

```bash
cd prototype-python
python -m pytest
```

The previous release's public API is covered by
`prototype-python/tests/test_public_api.py`.

## Installing the Previous Release

The last Python-only release (`astars` 0.1.0, pre-Rust-migration) is still
installable from PyPI and works as published:

```bash
pip install astars
```

```python
import astars

source = "def hello(name):\n    return name\n"

unit = astars.parse_str(source, lang="python")

print(unit.lang)
print(unit.root.kind)

function = unit.find(kind="FunctionDef")[0]

print(unit.span_of(function))
print(unit.source_of(function))
print(unit.node_at(4).kind)
```

Expected output:

```text
python
Module
SourceSpan(start_byte=0, end_byte=32, start_point=(0, 0), end_point=(1, 15))
def hello(name):
    return name
Identifier
```

Important public objects in that release: `astars.SourceUnit`,
`astars.SourceSpan`, `astars.Diagnostic`, `astars.AstarsError`,
`astars.UnsupportedLanguageError`, `astars.ParserUnavailableError`. This release
is frozen; new development happens in the Rust core and its bindings described
above.

## Design Documents

The current strategy and architecture notes are maintained in Japanese:

- [Current Action Items](docs/ACTION_ITEMS.ja.md)
- [Strategy](docs/STRATEGY.ja.md)
- [API Strategy](docs/API_STRATEGY.ja.md)
- [Concepts](docs/CONCEPTS.ja.md)
- [Architecture](docs/architecture/ARCHITECTURE.ja.md)
- [Edit Model](docs/architecture/EDIT_MODEL.ja.md)
- [Source Mapping Plan](docs/SOURCE_MAPPING_PLAN.ja.md)
- [Migration](docs/MIGRATION.ja.md)
- [Release Strategy](docs/RELEASE_STRATEGY.ja.md)
- [v0 Plan](docs/V0_PLAN.ja.md)
- [Next Release Plan](docs/NEXT_RELEASE_PLAN.ja.md)

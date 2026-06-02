<p align="center">
  <img src="https://raw.githubusercontent.com/xwasoux/astars/main/docs/assets/logo.png" alt="Astars logo" width="520">
</p>

<h1 align="center">Astars</h1>

<p align="center">
  <strong>A lightweight program-structure engine.</strong>
</p>

Astars parses source code into an AST-like structure, lets users inspect and query
that structure, and maps nodes back to their original source spans and source
text. Astars is intended to be a small engine that downstream packages can build
on, rather than a full analysis product by itself.

## Project Status

Astars 0.1.0 provides the first v0 public API.

The current v0 scope is intentionally small:

- parse Python source code
- inspect AST-like nodes without touching parser-specific objects
- find nodes by kind
- map nodes to byte spans and source text
- provide a stable entry point for downstream `astars-*` packages

The following are outside the v0 scope:

- source editing primitives
- semantic analysis
- multi-language support
- metrics, code review, pruning, or LLM-specific policies
- stable compatibility for legacy `AParser`, `APruner`, or `ATraverser` APIs

## Installation

Astars currently requires Python 3.10 or newer.

For the released package:

```bash
pip install astars
```

To try the development version from this repository:

```bash
git clone https://github.com/xwasoux/astars.git
cd astars
pip install -e .
```

## Quick Start

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

## Public API

Astars exposes the v0 API from the top-level `astars` package:

```python
import astars

unit = astars.parse_file("example.py", lang="python")
unit = astars.parse_str("x = 1\n", lang="python")
unit = astars.parse_bytes(b"x = 1\n", lang="python")
```

Each parse function returns a `SourceUnit`.

```python
root = unit.root
diagnostics = unit.diagnostics

for node in unit.walk():
    print(node.kind)

functions = unit.find(kind="FunctionDef")
node = unit.node_at(byte_offset=4)

span = unit.span_of(functions[0])
source_text = unit.source_of(functions[0])
```

Important public objects:

- `astars.SourceUnit`
- `astars.SourceSpan`
- `astars.Diagnostic`
- `astars.AstarsError`
- `astars.UnsupportedLanguageError`
- `astars.ParserUnavailableError`

## Design Boundary

Astars is an engine layer. It should answer questions such as:

- What is the program structure of this source file?
- Which nodes match this structural query?
- Where did this node come from in the original source?
- What source text corresponds to this node?

Astars should not decide what a metric means, whether a code review finding is
important, or which LLM evaluation policy should be applied. Those decisions
belong in downstream packages such as `astars-metrics`, `astars-code-review`, or
`astars-llm-eval`.

## Development

Run the test suite with:

```bash
python -m pytest
```

The v0 public API is covered by `tests/test_public_api.py`.

## Design Documents

The current strategy and architecture notes are maintained in Japanese:

- [Strategy](docs/STRATEGY.ja.md)
- [API Strategy](docs/API_STRATEGY.ja.md)
- [Concepts](docs/CONCEPTS.ja.md)
- [Architecture](docs/ARCHITECTURE.ja.md)
- [Source Mapping Plan](docs/SOURCE_MAPPING_PLAN.ja.md)
- [Migration](docs/MIGRATION.ja.md)
- [Release Strategy](docs/RELEASE_STRATEGY.ja.md)
- [v0 Plan](docs/V0_PLAN.ja.md)
- [Next Release Plan](docs/NEXT_RELEASE_PLAN.ja.md)

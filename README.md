<p align="center">
  <img src="https://raw.githubusercontent.com/xwasoux/astars/main/docs/assets/logo.png" alt="Astars logo" width="520">
</p>

<h1 align="center">Astars</h1>

<p align="center">
  <strong>A lightweight program-structure engine.</strong><br>
  <strong>軽量なプログラム構造エンジン。</strong>
</p>

<p align="center">
  <a href="#english">English</a> | <a href="#日本語">日本語</a>
</p>

---

## English

Astars parses source code into an AST-like structure, lets users inspect and query
that structure, map nodes back to their original source spans and source text, and
apply a minimal source-aware edit primitive. Astars is intended to be a small
engine that downstream packages can build on, rather than a full analysis product
by itself.

### Project Status

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

### Build From Source

Requires a recent Rust toolchain. Verify the core engine builds and tests on its
own first:

```bash
git clone https://github.com/xwasoux/astars.git
cd astars
cargo test --workspace
```

#### Python binding

```bash
cd bindings/python
python3 -m venv .venv && source .venv/bin/activate
pip install maturin
maturin develop
python3 ../../examples/python/basic_parse.py
```

#### Node binding

```bash
cd bindings/node
npm install
npm run build:debug
node ../../examples/node/basic-parse.js
```

Both example scripts walk through the full v0 surface (query API, the edit
primitive, `parse_bytes`/`parse_file`, diagnostics, and `point_at`) against the
same sample source, so their output lines up one-to-one.

### Quick Start

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

### Public API

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

### Design Boundary

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

### Development

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

### Installing the Previous Release

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

### Design Documents

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

<p align="right"><a href="#astars">↑ Top</a></p>

---

## 日本語

Astars はソースコードを AST-like な構造に parse し、その構造を inspect・query できるようにし、node を元の source span / source text に戻し、最小限の source-aware な edit primitive を提供する。Astars は、それ単体で完結した分析製品ではなく、downstream package が土台にできる小さな engine であることを狙っている。

### プロジェクトの状態

**Astars の core engine は Rust で書き直している最中**(`crates/astars-core`)で、Python と Node.js はその binding 経由の consumer という位置づけになる(このリポジトリの `bindings/python` / `bindings/node`)。方針の経緯は [`docs/STRATEGY.ja.md`](docs/STRATEGY.ja.md)、現在の状況は [`docs/ACTION_ITEMS.ja.md`](docs/ACTION_ITEMS.ja.md) を参照。

Rust core は Python/Node 両 binding を通して v0 scope を一通り実装済みである。ただし **PyPI / npm へはまだ公開していない** — 試すには下の [ソースからビルドする](#ソースからビルドする) を参照。以前公開していた純粋な Python 実装(PyPI 上の `astars` 0.1.0)は [`prototype-python/`](prototype-python/) に frozen reference として残しており、active development の対象ではない。そちらを使いたい場合は [以前のリリースをインストールする](#以前のリリースをインストールする) を参照。

現在の v0 scope(Rust core):

- Python source を文字列・raw bytes・ファイル(encoding 指定込み)から parse する
- AST-like な node を inspect する — tree-sitter の生 CST を 1:1 で使い、parser 固有のオブジェクトには一切触れない
- 木を walk し、kind で node を find し、byte offset に対応する最も具体的な node を特定する
- node を byte span・source text・0-based の line/column 位置に対応づける
- 最小限の edit primitive: node の source span を replace し、別の node がその編集の影響を受けずに残ったかを問い合わせる
- parser recovery による diagnostics(構文エラー)

以下は v0 scope の対象外:

- insert/delete 専用の編集メソッド、Piece Table、編集の系譜追跡、名前/kind ベースの node アドレス指定(edit primitive の v2 として計画中)
- selector DSL
- 安定版の CST / raw node 公開 API
- semantic analysis
- Python 以外の対象言語
- downstream package 自体(`astars-metrics`、`astars-code-review` など)

### ソースからビルドする

最近の Rust toolchain が必要。まず core engine 単体が build・test できることを確認する:

```bash
git clone https://github.com/xwasoux/astars.git
cd astars
cargo test --workspace
```

#### Python binding

```bash
cd bindings/python
python3 -m venv .venv && source .venv/bin/activate
pip install maturin
maturin develop
python3 ../../examples/python/basic_parse.py
```

#### Node binding

```bash
cd bindings/node
npm install
npm run build:debug
node ../../examples/node/basic-parse.js
```

どちらの example script も、同じ sample source に対して v0 の全機能(query API、edit primitive、`parse_bytes`/`parse_file`、diagnostics、`point_at`)を一通りデモしており、出力は1対1で対応している。

### Quick Start

Python、`import _astars` 経由(将来の `import astars` は、この native module を薄くラップする別パッケージになる予定):

```python
import _astars

tree = _astars.parse_str("def hello(name):\n    return name\n", _astars.PyLang.Python).tree

function = tree.find("function_definition")[0]
print(tree.span_of(function))      # (0, 32)
print(tree.source_of(function))    # 'def hello(name):\n    return name'
print(tree.point_at(0))            # (0, 0)
```

Node.js、`@astars/native` 経由:

```js
const { parseStr, JsLang } = require('@astars/native');

const tree = parseStr('def hello(name):\n    return name\n', JsLang.Python);

const [fn] = tree.find('function_definition');
console.log(tree.spanOf(fn));   // [0, 32]
console.log(tree.sourceOf(fn)); // 'def hello(name):\n    return name'
console.log(tree.pointAt(0));   // [0, 0]
```

### Public API

core engine(`astars-core`)は `Lang`、`ParseResult`、`SyntaxTree`(+ `NodeId`、`ByteSpan`、`Point`、`EditResult`、`Diagnostic`、`Severity`)、`parse_str` / `parse_bytes` / `parse_file` を公開している。各 binding はこの surface をそれぞれの言語の流儀でミラーする:

- Python(`_astars`): `PyLang`、`PyParseResult`、`PySyntaxTree`、`PyNodeInfo`、`PyEditResult`、`PyDiagnostic`、`parse_str` / `parse_bytes` / `parse_file`
- Node(`@astars/native`): `JsLang`、`JsSyntaxTree`、`JsNodeInfo`、`JsEditResult`、`JsDiagnostic`、`parseStr` / `parseBytes` / `parseFile`

各型のメソッド単位の詳細は、この README ではなく [`docs/architecture/ARCHITECTURE.ja.md`](docs/architecture/ARCHITECTURE.ja.md) の Mermaid クラス図を参照する。コードと同期する場所を一箇所にするためである。

### Design Boundary

Astars は engine layer である。次のような問いに答えるべきものである:

- この source file のプログラム構造は何か?
- この構造的な query にどの node がマッチするか?
- この node は元の source のどこから来たのか?
- この node に対応する source text は何か?
- この node を編集したら何が変わり、他の何が影響を受けずに残るか?

Astars は、metric が何を意味するか、code review の指摘が重要かどうか、どの LLM evaluation policy を適用すべきかを決めるべきではない。それらの判断は `astars-metrics`、`astars-code-review`、`astars-llm-eval` のような downstream package の責務である。

### Development

Rust workspace(`crates/astars-core`、`bindings/python`、`bindings/node`):

```bash
cargo test --workspace
cargo clippy --workspace -- -D warnings
```

core を変更した後に binding を再ビルドする:

```bash
# Python
cd bindings/python && source .venv/bin/activate && maturin develop

# Node
cd bindings/node && npm run build:debug
```

Python prototype(frozen reference、`prototype-python/` 配下):

```bash
cd prototype-python
python -m pytest
```

以前のリリースの public API は `prototype-python/tests/test_public_api.py` でカバーされている。

### 以前のリリースをインストールする

最後の Python only release(`astars` 0.1.0、Rust 移行前)は、今も PyPI からインストールでき、公開時のまま動作する:

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

期待される出力:

```text
python
Module
SourceSpan(start_byte=0, end_byte=32, start_point=(0, 0), end_point=(1, 15))
def hello(name):
    return name
Identifier
```

そのリリースにおける主な公開オブジェクト: `astars.SourceUnit`、`astars.SourceSpan`、`astars.Diagnostic`、`astars.AstarsError`、`astars.UnsupportedLanguageError`、`astars.ParserUnavailableError`。このリリースは frozen であり、新しい開発は上記の Rust core とその binding 側で行っている。

### Design Documents

現在の戦略・アーキテクチャに関するドキュメントは日本語で管理している:

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

<p align="right"><a href="#astars">↑ Top</a></p>

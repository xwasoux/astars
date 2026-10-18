# Astars アーキテクチャ

ステータス: Rust core 実装中(v0 spike 段階)

関連文書:

- [STRATEGY.ja.md](../STRATEGY.ja.md)
- [ACTION_ITEMS.ja.md](../ACTION_ITEMS.ja.md)
- [API_STRATEGY.ja.md](../API_STRATEGY.ja.md)
- [CONCEPTS.ja.md](../CONCEPTS.ja.md)
- [EDIT_MODEL.ja.md](EDIT_MODEL.ja.md): 編集時のテキスト/木の追従モデル(v0 scope の AST node 構造設計の前提)

関連図(`.drawio.svg`。VS Code の draw.io 拡張で開くと編集できる):

#### repo-structure: monorepo 構成の決定

![repo-structure](repo-structure.drawio.svg)

#### core-parse-spike: `crates/astars-core` の最小 parse spike クラス図

![core-parse-spike](core-parse-spike.drawio.svg)

#### python-binding-spike: `bindings/python`(pyo3)のクラス図

![python-binding-spike](python-binding-spike.drawio.svg)

#### node-binding-spike: `bindings/node`(napi-rs)のクラス図

![node-binding-spike](node-binding-spike.drawio.svg)

> 2026-05 〜 09 にかけて書かれていた旧版は、Python 実装(`astars/` package)を前提にした目標アーキテクチャだった。`STRATEGY.ja.md` で core engine の実装言語を Rust にする方針へ転換したため、本書はその旧版を置き換える形で Rust 構成向けに書き直している。旧 Python 実装は `prototype-python/` に frozen reference として残っており、そこで検証済みの設計判断(source mapping の挙動、tie-breaker 方針など)は `SOURCE_MAPPING_PLAN.ja.md` の Resolved Decisions を通じて引き継ぐ。

この文書は、Astars の概念モデルを実装上の crate / module boundary に落とすための文書である。現行コードをそのまま正当化する文書ではなく、`astars` engine として安定させるべき目標アーキテクチャを示す。

## Architecture Goals

Astars の architecture は、次の性質を満たすことを目指す。

- parser-specific API(tree-sitter)を core から隔離する
- binding-specific API(pyo3 / napi-rs)を core から隔離する — core は Rust だけに依存する
- source mapping を core value として扱う
- analysis-specific な判断を core に入れない
- downstream(Python ML research / Node agent framework)が依存しやすい小さな public API を持つ
- Python を reference 言語としつつ、他言語追加の余地を残す
- source-aware edit primitive を提供できる構造にする

## Repository Layout

monorepo 構成の決定は [repo-structure.drawio.svg](repo-structure.drawio.svg) を参照。実際に作成したディレクトリ構成は次の通り。

```text
astars/                      (repo root, Cargo workspace)
  Cargo.toml                 workspace manifest

  crates/
    astars-core/              parse / normalize / map / query / edit の core engine
      src/
        lib.rs                 public facade: Lang, ParseResult, parse_str()
        parse/                 internal module(非 pub。crate 外から不可視)
          mod.rs
          adapter.rs            ParseAdapter: tree-sitter を直接叩く唯一の場所
          raw_tree.rs           RawTree: tree_sitter::Tree を保持する internal struct

  bindings/
    python/                   crate `astars-py`、lib 名 `_astars`
      src/lib.rs               PyLang / PyParseResult(astars_core の mirror + convert)
      pyproject.toml           maturin build-backend
    node/                     crate `astars-node`、npm package `@astars/native`
      src/lib.rs               JsLang / JsParseResult(astars_core の mirror + convert)
      build.rs                 napi_build::setup()
      package.json              @napi-rs/cli

  prototype-python/          旧 Python 実装(frozen reference, 非 active development)

  docs/
    architecture/             本書 + draw.io 図
```

## Layer Overview

Astars は、概念的に次の layer に分ける。

```mermaid
flowchart TB
    PyConsumer["Python consumer\n(ML / research)"]
    NodeConsumer["Node consumer\n(coding agent framework)"]

    subgraph PyBinding["bindings/python (crate astars-py)"]
        PyFacade["_astars pymodule\nPyLang / PyParseResult"]
    end

    subgraph NodeBinding["bindings/node (crate astars-node)"]
        NodeFacade["@astars/native napi module\nJsLang / JsParseResult"]
    end

    subgraph Core["crates/astars-core"]
        PublicAPI["public facade\nLang / ParseResult / parse_str()"]
        subgraph ParseMod["parse (internal module)"]
            Adapter["ParseAdapter"]
            Raw["RawTree"]
        end
    end

    TreeSitter["tree-sitter crate (external)"]

    PyConsumer --> PyFacade
    NodeConsumer --> NodeFacade
    PyFacade -- convert + call --> PublicAPI
    NodeFacade -- convert + call --> PublicAPI
    PublicAPI --> Adapter
    Adapter --> Raw
    Raw --> TreeSitter
```

依存方向は、consumer(Python/Node)から binding crate に向かい、binding crate は `astars-core` の public facade だけに依存する。`astars-core` 自身は pyo3 にも napi-rs にも依存しない(binding-agnostic)。tree-sitter への依存は `astars-core` 内の `parse`(internal module)に閉じ込められ、`astars-core` の public API にも、binding crate にも漏れない。

## Dependency Direction

原則:

- Python / Node consumer は、それぞれの binding crate(`astars-py` / `astars-node`)にのみ依存する
- binding crate は `astars-core` の public facade(`Lang`, `ParseResult`, `parse_str`)にのみ依存する
- binding crate は、FFI 境界を越えるための mirror 型(`PyLang`/`JsLang` など)と変換ロジック(`From` 実装)を自分で持つ
- `astars-core` は pyo3 / napi-rs のどちらにも依存しない
- `astars-core` の public facade は `parse`(internal module)の実装詳細(tree-sitter 型)に依存させない
- `astars-core` は downstream package(`astars-metrics` 等、将来)に依存しない

依存方向を逆流させないことと、tree-sitter / pyo3 / napi-rs という3種の外部依存をそれぞれの層に閉じ込めることが、Astars を軽量 engine として保つための重要な制約である。

## Module Responsibilities

### `astars-core`(public facade, `src/lib.rs`)

public API の入口を提供する。

責務:

- `Lang`(対象言語の列挙)を公開する
- `ParseResult`(正規化された parse 結果)を公開する
- `parse_str(source, lang) -> ParseResult` を公開する
- `parse`(internal module)の実装詳細を隠す

### `astars-core::parse`(internal module)

parser 固有の処理を閉じ込める。crate root で `pub` にしていないため、crate 外からは `ParseAdapter` / `RawTree` のどちらにも到達できない。

責務:

- `ParseAdapter`: tree-sitter の `Parser` / `Language` を直接扱う唯一の場所
- `RawTree`: `tree_sitter::Tree` と source bytes を保持する internal struct
- tree-sitter 型を `astars-core` の public facade に漏らさない

### `bindings/python`(crate `astars-py`)

Python 向け FFI 層。pyo3 に依存してよい唯一の crate。

責務:

- `PyLang` / `PyParseResult`: `astars_core::Lang` / `ParseResult` の mirror 型
- `From` による双方向変換(`PyLang <-> Lang`, `ParseResult -> PyParseResult`)
- `#[pymodule] fn _astars(...)`: Python から `import _astars` で使う entry point
- `astars-core` を呼び出す(`astars_core::parse_str` の呼び出し)

### `bindings/node`(crate `astars-node`)

Node 向け FFI 層。napi-rs に依存してよい唯一の crate。

責務:

- `JsLang` / `JsParseResult`: `astars_core::Lang` / `ParseResult` の mirror 型(`JsParseResult` は `#[napi(object)]` の plain object)
- `From` による双方向変換
- `#[napi] fn parse_str(...)`: Node から `parseStr`(napi-rs の camelCase 規約)として呼ばれる entry point
- `astars-core` を呼び出す

### `prototype-python/`(frozen reference)

旧 Python 実装。active development の対象ではないが、source mapping の挙動・edge case・tie-breaker 方針などの設計判断は、Rust 実装の参照として使う。詳細は [`prototype-python/README.md`](../../prototype-python/README.md)。

## Public / Extension / Internal Boundary

### Public(`astars-core`)

downstream(binding crate)が依存してよいもの:

- `Lang`
- `ParseResult`
- `parse_str(source, lang) -> ParseResult`

### Public(各 binding crate)

consumer(Python / Node)が依存してよいもの:

- Python: `_astars.PyLang`, `_astars.PyParseResult`, `_astars.parse_str`
- Node: `JsLang`, `JsParseResult`, `parseStr`(`@astars/native` から)

### Internal

安定 API として扱わないもの:

- `astars-core::parse::ParseAdapter` / `RawTree`(crate 外から到達不可)
- `tree_sitter::Parser` / `Tree` / `Node` などの tree-sitter 型
- pyo3 / napi-rs の型(binding crate の実装詳細)

## v0 Scope(Rust core)

旧 Python 実装の `0.1.0` 相当(`astars.parse_str` / `SourceUnit` / `SourceSpan` / `Diagnostic` / node interface / `walk` / `find` / `node_at` / `span_of` / `source_of`)に、Rust core として到達することを `v0` のゴールとする。

### 現状(spike 段階)

- [x] `parse_str(source, lang) -> ParseResult { lang, node_count }` — toolchain(tree-sitter + pyo3 + napi-rs)が繋がることの証明が目的で、**機能的にはまだ Python 0.1.0 と同等ではない**
- [x] `astars-core` が binding-agnostic であることをコードレベルで保証(`mod parse;` が非 `pub`)
- [x] Python / Node 両 binding から実際に呼び出せることを確認済み

### 残っている作業(v0 到達に必要)

- [ ] AST-like node 構造(`astars-core` 内に node 型を持ち、`ParseResult` が node 数ではなく root node を返すようにする)。データ構造設計の前提は [EDIT_MODEL.ja.md](EDIT_MODEL.ja.md) を参照
- [ ] `SyntaxGraph` 相当(AST node ↔ raw span の対応)
- [ ] `SourceSpan` / `SourceText` 相当(byte offset、half-open span、UTF-8 境界の扱い。`prototype-python` の `SOURCE_MAPPING_PLAN.ja.md` Resolved Decisions を踏襲する)
- [ ] query API(`find(kind=...)`, `node_at(byte_offset)`)
- [ ] `parse_bytes` / `parse_file` の追加(現状 `parse_str` のみ)
- [ ] Diagnostics(parser recovery の `ERROR` / `MISSING` node を扱う)
- [ ] 各 binding crate に、上記を mirror する型を追加する

### Non-Goals(v0 では扱わない)

- edit primitive の本格実装
- CST / `RawSyntaxNode` の stable public API 化
- semantic analysis
- Python 以外の対象言語

## Open Questions

- AST node を `astars-core` の public facade でどう表現するか(所有権を Rust 側に置き、binding 層からは handle/index でアクセスさせる想定だが、具体形は未決定)
- `SyntaxGraph` を `astars-core` 内の別 internal module にするか、`parse` module に含めるか
- Python / Node 両方で同じ node id 安定性(stable ID)をどう保証するか
- edit primitive をいつ設計に着手するか(`STRATEGY.ja.md` の Open Questions 参照)

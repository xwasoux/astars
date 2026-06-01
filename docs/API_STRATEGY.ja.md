# Astars API 戦略

ステータス: draft

関連文書:

- [STRATEGY.ja.md](STRATEGY.ja.md)
- [CONCEPTS.ja.md](CONCEPTS.ja.md)
- [ARCHITECTURE.ja.md](ARCHITECTURE.ja.md)
- [MIGRATION.ja.md](MIGRATION.ja.md)

この文書は、軽量な program-structure engine としての Astars の API 戦略を定義する。目的は、downstream の `astars-*` package が安心して依存できる表面を作りつつ、parser 固有の詳細や application-specific な判断を public API から切り離すことである。

## 目的

Astars API は、core engine と downstream analysis module の間の契約である。

downstream package は、この API を通じて source code を parse し、program structure を inspect し、node を source span に戻し、generic な source-aware operation を組み立てられるべきである。

API は次の性質を持つべきである。

- 小さく、学びやすい
- downstream package が依存できる程度に安定している
- source mapping を明示的に扱う
- analysis meaning について中立である
- public / extension-level / internal の境界が明確である

## 想定ユーザー

### Downstream Package Authors

`astars-metrics`, `astars-code-review`, `astars-pruning`, `astars-llm-eval` などを書くユーザー。

この層のユーザーには安定した契約が必要である。通常の分析 workflow では、adapter internals、rule builders、parser objects を import する必要がない状態を目指す。

### Research Prototype Authors

notebook、script、実験コードで source code を素早く parse、inspect、query、transform したいユーザー。

この層のユーザーには、単純な top-level function と読みやすい data structure が必要である。

### Language Extension Authors

別言語のサポートを追加したいユーザー。

この層には、adapter、rule registry、normalization logic のための extension API が必要になる。ただし、それは stable public API とは分けて文書化する。

### Engine Contributors

Astars 自体を実装する開発者。

この層のユーザーは internal module に触ることがある。ただし、repository に存在する module がそのまま implicit public API になるべきではない。

## API レイヤー

Astars は、概念的に 3 つの API レイヤーを持つ。

### Stable Public API

stable public API は、downstream package が通常依存してよい API である。

`astars` 直下、または文書化された public submodule から import できるようにする。

例:

- `astars.parse_file`
- `astars.parse_str`
- `astars.parse_bytes`
- public result object
- public AST node interface
- public source span interface
- public query/traversal helpers

### Extension API

extension API は、言語追加や normalization behavior の変更のための API である。

adapter contract、rule registry contract、language support hook などを含む可能性がある。stable public API より速く変化してよいが、contributor が使える程度には文書化する。

### Internal API

internal API は実装詳細である。

parser-specific object、raw tree-sitter node、rule builder internals、cache internals は stable ではない。downstream package は、意図的に破壊的変更を受け入れる場合を除き、これらに依存しない。

## Primary Workflows

public API は、次の workflow を中心に設計する。

### Source を Parse する

```python
import astars

unit = astars.parse_file("example.py", lang="python")
unit = astars.parse_str("x = 1\n", lang="python")
unit = astars.parse_bytes(b"x = 1\n", lang="python")
```

parse result は、source、AST、mapping、diagnostics、query helper を持つ main handle になるべきである。

### Structure を Inspect する

```python
root = unit.root

for node in unit.walk():
    print(node.kind)
```

ユーザーは、tree-sitter object に依存せずに AST-like structure を inspect できるべきである。

### Node を Query する

```python
functions = unit.find(kind="FunctionDef")
node = unit.node_at(byte_offset=42)
```

query API は、一般的な分析 workflow をカバーしつつ、domain-specific になりすぎないようにする。

### Node を Source に戻す

```python
span = unit.span_of(node)
source = unit.source_of(node)
```

node から source への mapping は、first-class public workflow として扱う。

### Source-Aware Operation を組み立てる

```python
edit = unit.edit.delete(node)
new_source = edit.apply()
```

core は generic edit primitive を提供してよい。ただし、どの node を編集対象にするかという domain-specific な判断は Astars core の外に置く。

この workflow は重要だが、最初に固定する public API には含めない。まず parse、inspect、query、source mapping を安定させ、その後に edit primitive を追加する。

## Initial Public API

この節は、`MIGRATION.ja.md` の Phase 1 で最初に実装・固定する public API を定義する。

v0 の public API は、source code を parse し、AST-like node を inspect/query し、node を source span に戻すところまでを対象にする。source-aware edit primitive は次段階の API として扱う。

### v0 で固定する API

v0 では、次の名前を `astars` 直下から import できるようにする。

- `astars.parse_file`
- `astars.parse_str`
- `astars.parse_bytes`
- `astars.SourceUnit`
- `astars.SourceSpan`
- `astars.Diagnostic`
- `astars.AstarsError`
- `astars.UnsupportedLanguageError`
- `astars.ParserUnavailableError`
- `astars.__version__`

AST node の concrete class 名は v0 では強く固定しない。ただし、public node interface は固定する。

### Parse Functions

最初の parse API は、次の形を基本とする。

```python
unit = astars.parse_file(path, *, lang, encoding="utf-8")
unit = astars.parse_str(source, *, lang, path=None)
unit = astars.parse_bytes(source_bytes, *, lang, path=None)
```

方針:

- `lang` は keyword-only かつ必須にする
- file extension からの language 推定は v0 では必須機能にしない
- 汎用的な `options` bag は v0 では公開しない
- `path` は source location を保持するための任意 metadata として扱う
- 3 つの parse function は同じ `SourceUnit` を返す

`options` は便利だが、意味が曖昧なまま public API に入れると将来の互換性を壊しやすい。必要な option が明確になった時点で、名前付き引数または extension API として追加する。

### SourceUnit Interface

`SourceUnit` は、1つの source input を parse した結果全体を表す public handle として採用する。

v0 で固定する property / method:

- `unit.lang`
- `unit.path`
- `unit.source`
- `unit.root`
- `unit.diagnostics`
- `unit.walk(kind=None)`
- `unit.find(kind=None)`
- `unit.node_at(byte_offset)`
- `unit.span_of(node)`
- `unit.source_of(node)`

方針:

- `unit.root` は AST-like root node を返す
- `unit.walk()` は `unit.root` からの depth-first traversal を返す
- `unit.find(kind="FunctionDef")` は kind による最小 query として始める
- `unit.node_at(byte_offset)` は byte offset から最も対応する node を返す
- `unit.span_of(node)` は `SourceSpan` または `None` を返す
- `unit.source_of(node)` は node に対応する source text を返す

query 条件は、最初は `kind` に絞る。`role`、`name`、predicate、selector DSL は、実際の downstream use case が見えてから追加する。

### Public Node Interface

v0 の node object は、少なくとも次の属性を持つ。

- `node.kind`
- `node.id`
- `node.children`
- `node.role`
- `node.value`

必須:

- `kind`
- `id`
- `children`

任意:

- `role`
- `value`

`node.id` は、1つの `SourceUnit` の中で node を識別するための ID とする。v0 では、edit をまたいだ永続 ID や Astars version をまたいだ stable ID は保証しない。

### SourceSpan Interface

`SourceSpan` は、source code 上の範囲を表す public object として採用する。

v0 で固定する属性:

- `span.start_byte`
- `span.end_byte`
- `span.start_point`
- `span.end_point`

方針:

- byte offset を canonical representation とする
- `start_point` / `end_point` は 0-based の `(line, column)` とする
- line は 0-based line number とする
- column は byte column を基本とし、Unicode column 表示は別 helper の候補とする

人間向け表示や review comment では 1-based line number が必要になることがある。その変換は helper として提供してよいが、engine 内部と public span object の基準は 0-based に揃える。

### Diagnostics Interface

`Diagnostic` は、parse や normalization の問題を表す public object として扱う。

v0 で固定する属性:

- `diagnostic.severity`
- `diagnostic.message`
- `diagnostic.span`

方針:

- syntax error のように parser が recovery できる問題は、可能な限り `unit.diagnostics` に載せる
- unsupported language や parser dependency missing は exception として扱う
- `span` が特定できない diagnostic では `span=None` を許容する

### v0 では固定しない API

次の API は重要だが、v0 の固定対象から外す。

- CST の stable public API
- `RawSyntaxNode` の public API
- parser adapter contract
- language extension API
- edit primitive
- selector DSL
- semantic analysis API
- legacy `AParser` / `APruner` / `ATraverser`

これらは extension-level または次段階の API として設計する。

## Proposed Public Surface

この節は、v0 の後に拡張する候補を含む提案である。`Initial Public API` と矛盾する場合は、`Initial Public API` を優先する。

### Top-Level Functions

Astars は、小さな top-level parse API を提供する。

- `astars.parse_file(path, *, lang, encoding="utf-8")`
- `astars.parse_str(source, *, lang, path=None)`
- `astars.parse_bytes(source_bytes, *, lang, path=None)`

これらの関数は、同じ種類の result object を返す。

### Primary Result Object

parse result は、高レベルな source unit object であるべきである。

parse result は `SourceUnit` と呼ぶ。これは、1 つの source input と、その構造、mapping、diagnostics をまとめた単位である。

必要な public capability:

- `unit.lang`
- `unit.path`
- `unit.source`
- `unit.root`
- `unit.diagnostics`
- `unit.walk(...)`
- `unit.find(...)`
- `unit.node_at(...)`
- `unit.span_of(node)`
- `unit.source_of(node)`

通常の workflow では、parser-specific tree にアクセスする必要がない設計にする。

### AST Node Interface

AST node は、小さく安定した interface を公開する。

- `node.kind`
- `node.id` または `node.stable_id`
- `node.role`
- `node.value`
- `node.children`

保存方法の詳細は internal とする。Astars が内部で `anytree` を使うとしても、downstream package に `anytree` API への依存を強制しない。

### Source Span Interface

source span は、public API では匿名 tuple ではなく明示的な object として扱う。

span は少なくとも次を持つ。

- `start_byte`
- `end_byte`
- `start_point`
- `end_point`

byte offset を canonical representation とする。`start_point` / `end_point` は 0-based の `(line, column)` とし、column は byte column を基本とする。

### Diagnostics

syntax error を含む source を parse した場合、可能であれば常に exception を投げるのではなく、diagnostics を持つ result を返す。

exception は次のような失敗に使う。

- unsupported language
- missing parser dependency
- invalid input type
- unrecoverable parser failure

### Version Information

Astars は自身の version を公開する。

```python
astars.__version__
```

downstream package は、対応する Astars engine version を宣言できるべきである。

## Public vs Internal Objects

### Public By Default

downstream package が依存してよいもの:

- top-level parse functions
- primary result object
- AST node interface
- source span interface
- public query/traversal helpers
- edit API 導入後に文書化された generic edit primitives

### Extension-Level

文書化するが、public API より変化を許容するもの:

- language adapter contracts
- AST rule contracts
- normalization hooks
- language registry APIs

### Internal By Default

stable public API ではないもの:

- tree-sitter node objects
- tree-sitter parser objects
- raw parser caches
- concrete rule builder internals
- private mapping indexes
- vendored grammar files
- implementation-specific tree libraries

## Compatibility Strategy

### Legacy Names

`AParser`, `APruner`, `ATraverser` のような legacy name は、新 API を定義する中心にしない。

考えられる方針:

- `AParser` は、一時的な compatibility wrapper として再導入してもよい。
- `APruner` は domain-specific pruning strategy を表すなら core の外へ移す。
- `ATraverser` は generic traversal primitive に置き換える。

新しい downstream package は、legacy `A*` API ではなく新 API を対象にする。

### Breaking Changes

`1.0` 以前は、engine surface を安定させる過程で breaking change が発生してよい。

ただし `1.0` 以前であっても、次に影響する breaking change は文書化する。

- top-level parse functions
- result object shape
- node interface
- span semantics
- language support behavior

`1.0` 以降の public API change は deprecation policy に従う。

## Guarantees

### Source Mapping Guarantees

parser が十分な情報を提供する場合、Astars は public node を source span に戻せることを保証する。

node を mapping できない場合は、無効な span を黙って返すのではなく、`None` または文書化された missing span value を返す。

### Stable ID Guarantees

Astars は、"stable" の意味を慎重に定義する。

初期保証:

- node ID は 1 つの parsed source unit の中で安定している
- 同じ source、language、Astars version、rule set であれば、可能な限り deterministic である

初期には保証しないもの:

- 任意の edit をまたいだ stable ID
- Astars version をまたいだ stable ID
- language rule の変更をまたいだ stable ID

### Node Kind Guarantees

node kind は、downstream analysis package が依存できる程度に安定させる。

`astars-metrics` や `astars-code-review` のような package は node kind に依存する可能性があるため、public node kind の変更は API change として扱う。

### Parser Isolation Guarantees

通常の public workflow は、tree-sitter-specific object を必要としない。

Astars が debug 用に parser data への access を提供する場合、その access は unstable または advanced として明示する。

## Downstream Package Guidance

downstream package は次の方針に従う。

- documented public API に依存する
- 可能な限り parsed source unit を入力として受け取る
- parser adapter を直接 import しない
- private node storage detail に依存しない
- 対応する Astars version を文書化する

望ましい downstream の形:

```python
import astars

def collect_metrics(unit: astars.SourceUnit) -> dict:
    return {
        "functions": len(unit.find(kind="FunctionDef")),
    }
```

downstream package は、可能であれば source path や raw source ではなく `SourceUnit` を受け取る形にする。

## Non-Goals

API は次のものを公開しない。

- full semantic analysis framework
- review decisions
- metrics definitions
- pruning policies
- visualization-specific objects
- 必須 workflow dependency としての parser-specific objects

## Open Questions

- `CST` は stable public API に含めるべきか
- `RawSyntaxNode` は public, extension-level, internal のどれに置くべきか
- traversal は result object の method、standalone function、あるいは両方として公開するべきか
- edit primitive は text を直接返すべきか、edit plan を返すべきか、新しい parsed source unit を返すべきか
- language extension API は `1.0` 前にどこまで stable にするべきか
- `stable_id` の保証が限定的な場合、名前を変えるべきか
- Unicode code point / grapheme cluster ベースの column 表示を public helper として提供するべきか

## 成功条件

API 戦略がうまく機能している状態とは、downstream package が次を実現できる状態である。

1. `astars` を使って source を parse できる
2. 文書化された API で node を traverse/query できる
3. node を source span に戻せる
4. parser object への直接依存を避けられる
5. unrelated な `astars-*` package を install せずに Astars に依存できる
6. minor engine update のたびに import を書き換えなくてよい

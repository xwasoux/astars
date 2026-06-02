# Astars Source Mapping 計画

ステータス: `0.2.0` primary theme draft

関連文書:

- [STRATEGY.ja.md](STRATEGY.ja.md)
- [CONCEPTS.ja.md](CONCEPTS.ja.md)
- [API_STRATEGY.ja.md](API_STRATEGY.ja.md)
- [ARCHITECTURE.ja.md](ARCHITECTURE.ja.md)
- [NEXT_RELEASE_PLAN.ja.md](NEXT_RELEASE_PLAN.ja.md)

この文書は、`0.2.0` の主テーマである source mapping 安定化について、public behavior と internal responsibility を分けて整理する。

Astars の価値は、AST-like node を作ることだけではなく、その node を元 source の byte range / text / position に戻せることにある。source mapping は補助機能ではなく、query、diagnostics、edit primitive、downstream finding の共通基盤として扱う。

## Goal

`0.2.0` では、次の workflow をより信頼できる public behavior として固定する。

```python
import astars

unit = astars.parse_str("def hello(name):\n    return name\n", lang="python")
function = unit.find(kind="FunctionDef")[0]

span = unit.span_of(function)
source = unit.source_of(function)
node = unit.node_at(span.start_byte)
```

この workflow について、次を明確にする。

- byte offset / point / source slice の基準
- mapping できない node の扱い
- invalid offset の扱い
- zero-width span の扱い
- encoding / Unicode source の扱い
- internal model の責務分担

## Non-Goals

`0.2.0` source mapping では、次を主目的にしない。

- edit primitive の本格実装
- selector DSL の追加
- CST / `RawSyntaxNode` の stable public API 化
- semantic analysis
- multi-language support
- source formatting / whitespace / comments の lossless transform 保証

ただし、edit primitive の設計に必要な前提は、この文書で整理する。

## Public Behavior

public behavior は、downstream package が依存してよい挙動である。`SourceUnit`、`SourceSpan`、diagnostics、AST-like node interface を中心に定義する。

### SourceSpan

`SourceSpan` は source code 上の範囲を表す public object である。

現行属性:

- `start_byte`
- `end_byte`
- `start_point`
- `end_point`

`0.2.0` で固定したい挙動:

- byte offset を canonical representation とする
- `start_byte` と `end_byte` は UTF-8 encoded source bytes に対する 0-based offset とする
- `start_byte <= end_byte` を満たす
- `start_point` と `end_point` は 0-based `(line, column)` とする
- `column` は byte column とする
- `end_byte` は half-open range の終端とする
- `SourceSpan(0, 0, (0, 0), (0, 0))` のような zero-width span を許容する

`0.2.0` では固定しないもの:

- Unicode code point column
- grapheme cluster column
- display width column
- 1-based line / column
- file URI や repository-relative path を含む location object

これらは human-readable helper として後から追加できるが、`SourceSpan` の基準は byte offset に寄せる。

### SourceUnit.source

`SourceUnit.source` は parse input を text として保持する。

挙動:

- `parse_str` では渡された `str` を保持する
- `parse_bytes` では bytes を UTF-8 decode した text を保持する
- `parse_file(..., encoding=...)` では指定 encoding で decode した text を保持する
- decode できない byte は `errors="replace"` の方針を維持する

注意:

- public source text と internal mapping bytes は対応している必要がある
- `parse_file` で non-UTF-8 encoding を使った場合でも、mapping の canonical bytes は UTF-8 encoded source text を基準にする

### unit.span_of(node)

`unit.span_of(node)` は、AST-like node に対応する source span を返す。

挙動:

- mapping が存在する場合は `SourceSpan` を返す
- mapping が存在しない場合は `None` を返す
- invalid span を捏造しない
- parser-specific object を返さない
- `node` が同じ `SourceUnit` に属しているか検証するかは `0.2.0` で判断する

`None` になる候補:

- synthetic node
- root から source span を定義できない node
- mapping graph に AST node id が存在しない node
- mapping graph に raw span が存在しない node
- 別の `SourceUnit` 由来の node

未決定:

- 別 `SourceUnit` の node に対して `None` を返すか、`AstarsError` を投げるか
- source span が複数の不連続 range になる node を、covering span で表すか、将来 `SourceSelection` のような別 concept にするか

### unit.source_of(node)

`unit.source_of(node)` は、`unit.span_of(node)` で得た span に対応する source text を返す。

挙動:

- span が存在する場合は source bytes slice を UTF-8 decode して返す
- span が存在しない場合は `None` を返す
- `SourceSpan` の half-open byte range を使う
- source slice の意味は node の semantic value ではなく、元 source 上の対応範囲である

注意:

- trailing newline を含むかどうかは parser mapping の raw span に依存する
- formatting や whitespace を正規化しない
- text extraction は source mapping の public workflow であり、downstream package が parser object に触らず使える必要がある

### unit.node_at(byte_offset)

`unit.node_at(byte_offset)` は、byte offset を覆う最も具体的な AST-like node を返す。

`0.2.0` で固定したい挙動:

- input は UTF-8 encoded source bytes に対する byte offset とする
- offset が source 内の node span に含まれる場合、最も具体的な node を返す
- 該当 node がない場合は `None` を返す
- parser-specific object を返さない

境界の扱い:

- span は `[start_byte, end_byte)` として扱う
- `start_byte <= byte_offset < end_byte` の場合に含まれる
- `byte_offset == end_byte` はその span には含まれない
- EOF offset の扱いは `0.2.0` で test として固定する

未決定:

- negative offset や source length より大きい offset を `None` にするか、`AstarsError` にするか
- zero-width span に対して `node_at` が node を返すべきか
- 同じ span length の候補が複数ある場合の tie-breaker

### Diagnostics Span

`Diagnostic.span` も `SourceSpan` を使う。

挙動:

- parser recovery の `ERROR` / `MISSING` node を source span に戻す
- span が特定できない diagnostic は `span=None` を許容する
- missing syntax node のような zero-width diagnostic span を許容する

## Internal Responsibility

internal responsibility は、public behavior を支える実装上の責務である。downstream package が直接依存するべきではない。

### SourceText

`SourceText` は、source bytes/text と位置変換を扱う internal model として整理する候補である。

責務:

- original text を保持する
- canonical UTF-8 bytes を保持する
- byte offset と 0-based point を相互変換する
- byte range から source slice を取得する
- invalid offset / range の validation 方針を一箇所に集める

`SourceText` に寄せたい処理:

- `_byte_offset_to_point`
- source bytes slice
- encoding normalization
- source length / EOF offset 判定

`SourceText` に入れないもの:

- AST traversal
- query logic
- parser-specific node handling
- edit policy

### SourceSpan Construction

`SourceSpan` の生成は、raw byte range と `SourceText` の point conversion から行う。

責務:

- raw span `(start_byte, end_byte)` を validation する
- point を canonical bytes から計算する
- public `SourceSpan` を返す

方針:

- span validation を各 method に散らさない
- invalid span は早期に検出する
- public API に返す前に `SourceSpan` として整形する

### SyntaxGraph

`SyntaxGraph` は AST node id、raw origin id、byte span の対応関係を保持する。

責務:

- AST node id から raw origin ids を引く
- raw origin id から byte span を引く
- AST node id から covering byte span を計算する
- byte offset から raw / AST candidate を引く
- role-based mapping の下地を保持する

`0.2.0` で見直したい点:

- `span_of_ast` の covering span の意味を明文化する
- `ast_at` の tie-breaker を test で固定する
- zero-width raw span を position query でどう扱うかを決める
- mapping failure を diagnostics に載せるか、public method の `None` に留めるかを決める

### AST Builder / Rules

AST builder と rule は、AST node と raw source span の対応を失わないように mapping edge を作る。

責務:

- AST node id を決める
- AST node と raw origin id を link する
- role がある場合は role を link に残す
- synthetic node を作る場合、mapping 不能であることを明示する

注意:

- AST node を analysis-friendly にするために raw syntax をまとめることは許容する
- ただし source mapping が不明になる場合は、無効 span を作らない

### SourceUnit

`SourceUnit` は public handle として、internal model を組み合わせる。

責務:

- public method の入口になる
- AST traversal / query を提供する
- `SourceText` と `SyntaxGraph` を使って `SourceSpan` / source slice を返す
- internal graph や parser object をそのまま公開しない

`0.2.0` で整理したい点:

- `_source_bytes` 直接保持から `SourceText` へ寄せるか
- `_graph` の型を具体化するか
- node ownership validation を追加するか
- `span_of` / `source_of` / `node_at` の validation を一貫させるか

### Parser Adapter

parser adapter は parser-specific object を Astars-owned structure に変換する。

責務:

- source bytes を parser に渡す
- parser tree を `RawSyntaxNode` 相当に変換する
- raw node に byte span を保持する
- parser-specific object を public API に漏らさない

## Test Strategy

`0.2.0` では、source mapping を public behavior として test で固定する。

追加したい test:

- empty source
- EOF offset
- negative offset
- source length より大きい offset
- zero-width diagnostic span
- Unicode source の byte column
- non-UTF-8 file encoding
- nested function / class の `node_at`
- span boundary の half-open behavior
- mapping missing node の `span_of` / `source_of`
- same-span candidate の tie-breaker

優先度:

1. public behavior に関わる edge case
2. encoding / Unicode
3. position lookup
4. internal refactor safety

## Implementation Order

推奨順序:

1. public behavior を test に落とす
2. `SourceText` internal model を追加する
3. `SourceUnit` の source mapping 処理を `SourceText` 経由にする
4. `SyntaxGraph.ast_at` / span boundary の仕様を test で固定する
5. mapping failure の扱いを `None` / error / diagnostic のどれにするか決める
6. docs と README の source mapping 説明を更新する

## Acceptance Criteria

`0.2.0` source mapping 安定化は、次を満たしたら一段落とみなす。

- `SourceSpan` の byte offset / point semantics が文書化されている
- `unit.span_of(node)` の `None` 条件が文書化されている
- `unit.source_of(node)` の source slice semantics が文書化されている
- `unit.node_at(byte_offset)` の boundary behavior が test で固定されている
- Unicode / encoding の source mapping test がある
- zero-width span の扱いが diagnostics と position lookup で整理されている
- internal `SourceText` / `SyntaxGraph` / `SourceUnit` の責務が分かれている

## Open Questions

- invalid offset は `None` か `AstarsError` か
- 別 `SourceUnit` 由来 node は `None` か `AstarsError` か
- `node_at` は EOF offset をどう扱うか
- zero-width span は `node_at` の対象に含めるか
- covering span で不連続な raw spans を表してよいか
- human-readable 1-based location helper を public API に追加するか
- `SourceText` を public API に含めるか、internal に留めるか

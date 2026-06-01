# Astars 次期リリース計画

ステータス: draft

関連文書:

- [V0_PLAN.ja.md](V0_PLAN.ja.md)
- [ROADMAP.ja.md](ROADMAP.ja.md)
- [API_STRATEGY.ja.md](API_STRATEGY.ja.md)
- [RELEASE_STRATEGY.ja.md](RELEASE_STRATEGY.ja.md)

この文書は、`0.1.0` release 後の作業を、patch release で扱う保守作業と、minor release で扱う機能拡張に分けるための計画である。

## Current Baseline

`0.1.0` では、v0 public API の最小 workflow が成立した。

実装済み:

- `astars.parse_str`
- `astars.parse_bytes`
- `astars.parse_file`
- `SourceUnit`
- `SourceSpan`
- `Diagnostic`
- public node interface
- `unit.walk(kind=None)`
- `unit.find(kind=None)`
- `unit.node_at(byte_offset)`
- `unit.span_of(node)`
- `unit.source_of(node)`
- Python source の parse path
- AST-like node から source span / source text への mapping
- tree-sitter recovery diagnostics の最小実装
- README / example / release tooling の更新
- PyPI release workflow

未実装、または意図的に v0.1 から外したもの:

- edit primitive
- stable CST public API
- stable `RawSyntaxNode` public API
- selector DSL
- semantic analysis
- multi-language support
- legacy `AParser` / `APruner` / `ATraverser` compatibility
- downstream package 本体

## Release Line Policy

`0.1.x` は、`0.1.0` の public API を大きく広げず、release 品質と利用開始時の摩擦を下げるための line とする。

`0.2.0` は、downstream package がより自然に Astars を使えるようにするための engine capability を追加する line とする。

原則:

- `0.1.1` は bug fix、documentation fix、packaging fix を中心にする
- `0.1.1` では新しい大きな public concept を追加しない
- `0.2.0` では public API の小さな拡張を許容する
- edit primitive は重要だが、source mapping と query/traversal の安定性を崩してまで急がない

## 0.1.1 Maintenance Scope

`0.1.1` の目的は、`0.1.0` を使い始める人にとっての粗さを減らすことである。

候補:

- documentation status の整理
  - `v0 実装中` などの release 前表現を更新する
  - 存在しない英語版リンクや古い参照を取り除く
  - `0.1.0` release 後の正しい starting point を明示する
- release tooling の改善
  - `build` / `twine` がない場合の error message をわかりやすくする
  - TestPyPI / PyPI publish 前の手順を再現しやすくする
  - clean install smoke test の手順を文書化または script 化する
- packaging metadata の確認
  - README rendering
  - logo asset の参照
  - `MANIFEST.in`
  - sdist / wheel の内容
- public API regression の補強
  - `0.1.0` で固定した workflow の test を落とさない
  - source span / diagnostics の既知 edge case を bug fix として扱う
- release branch 運用の後処理
  - `main` / `develop` / tag / PyPI version が一致していることを確認する

`0.1.1` でやらないもの:

- edit primitive の追加
- selector DSL の追加
- second language support
- CST / `RawSyntaxNode` の stable public API 化
- legacy API compatibility の本格復活

## 0.2.0 Feature Scope

`0.2.0` の目的は、Astars を downstream package の engine として使いやすくすることである。

候補となるテーマ:

### 1. Query / Traversal の整理

`SourceUnit` の `walk` / `find` は残しつつ、内部的には engine operation として整理する。

候補:

- `operations/query` の設計
- `operations/traversal` の設計
- `kind` 以外の filter を追加するか判断する
- query result と source span mapping の組み合わせを使いやすくする

注意:

- selector DSL を急いで作らない
- domain-specific query は downstream package に置く

### 2. Source Model / Mapping の安定化

Astars の中核価値である node-to-source mapping をより信頼できるものにする。

候補:

- `SourceText` を internal model として整理する
- byte offset / point / source slice の責務を分離する
- mapping failure の扱いを明確にする
- human-readable location helper を追加するか判断する
- Unicode source の扱いを test で補強する

### 3. Extension-Level Contract の文書化

stable public API とは分けて、言語追加や adapter 実装のための contract を整理する。

候補:

- parser adapter contract
- `RawSyntaxNode` contract
- AST rule contract
- language registry の最小設計
- Python reference implementation の境界整理

### 4. Public Node Interface の強化

downstream package が node に依存しやすいように、node interface の保証を明確にする。

候補:

- `node.kind`
- `node.id`
- `node.children`
- `node.role`
- `node.value`
- node kind naming の方針
- 主要 Python node kind の regression test

### 5. Edit Primitive の設計 Spike

edit primitive は Astars の独自性に直結するが、`0.2.0` ではまず設計を固定することを優先する。

検討する問い:

- edit は text を直接返すか
- edit plan を返すか
- edit 後の `SourceUnit` を返すか
- delete / replace / extract の最小単位は何か
- formatting / comments / whitespace をどこまで保証するか

`0.2.0` で実装する場合も、最初は generic primitive に限定し、pruning policy や review policy は core に入れない。

### 6. Downstream Prototype

Astars core が downstream から自然に使えるかを検証するため、軽い prototype を作る。

候補:

- function / class metrics example
- LLM context extraction example
- source span 付き finding example

これは `astars-metrics` などの正式 package にする前の検証として扱う。

## Recommended Priority

次の順で進めるのが安全である。

1. `0.1.1` で documentation / release tooling / packaging の粗さを取る
2. `0.2.0` の primary theme を 1 つ選ぶ
3. `0.2.0` では query / traversal と source mapping の安定化を優先する
4. edit primitive は設計 spike を先に行い、実装範囲を小さく切る

理由:

- `0.1.0` はすでに parse / inspect / source mapping の縦切りが成立している
- 先に保守性を上げると、`0.2.0` の差分が読みやすくなる
- edit primitive は価値が大きい一方で、source mapping の設計に強く依存する

## Decision Gates

### `0.1.1` に進む条件

- `main` / `develop` / PyPI の状態が一致している
- `0.1.0` の release 後に見つかった文書・配布・install の問題が整理されている
- public API の behavior を変えずに直せる範囲である

### `0.2.0` に進む条件

- `0.2.0` の primary theme が 1 つに絞られている
- public API に追加する名前と、追加しない名前が分かれている
- `0.1.x` line に戻すべき bug fix と混ざっていない

## Open Questions

- `0.2.0` の primary theme は query / traversal か、source mapping か、edit primitive か
- `operations/` package を `0.2.0` で作るか、もう少し `SourceUnit` method に閉じるか
- `RawSyntaxNode` を extension-level として文書化する時期はいつか
- `0.2.0` に downstream prototype を含めるか、別 branch / 別 repository で扱うか

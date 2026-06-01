# Astars ロードマップ

ステータス: 継続更新中

関連戦略: [STRATEGY.ja.md](STRATEGY.ja.md)

この文書は、Astars の導入ストーリーと近い実装戦略を整理する。

リリース単位の直近計画は [NEXT_RELEASE_PLAN.ja.md](NEXT_RELEASE_PLAN.ja.md) で管理する。

## 導入ストーリー

Astars の導入は、いきなり大きな ecosystem を作るのではなく、小さな engine workflow から始める。

### Step 1: Parse And Inspect

まず、Python source を parse し、AST-like structure を inspect できる状態にする。

この段階で重要なのは、downstream user が tree-sitter object を直接触らなくても、node kind、children、source span を扱えることである。

### Step 2: Query And Source Mapping

次に、function、class、import、statement などを query し、それらを source span に戻せるようにする。

この段階で、metrics、review、LLM context extraction などの下流ユースケースが prototype として成立し始める。

### Step 3: Generic Edit Primitives

node に対応する source span の削除、置換、抽出など、generic な edit primitive を提供する。

この段階で重要なのは、Astars core が「何を編集すべきか」は決めず、「選ばれた node を source にどう反映するか」を支えることである。

### Step 4: Downstream Package 化

特定の分析目的が見えてきたら、`astars-metrics`, `astars-code-review`, `astars-pruning` のような downstream package に分ける。

core に入れるべきか迷った機能は、「他のユースケースでも使える primitive か」「特定の分析判断か」で分ける。

### Step 5: Language Expansion

Python reference path が安定したら、second language を使って adapter contract と AST rule contract を検証する。

この段階でも、downstream package が parser-specific API を直接学ばなくてよい状態を保つ。


## 近い戦略

### Release 0.1.1: Maintenance

`0.1.1` は、`0.1.0` の public API を大きく広げず、release 品質と導入時の摩擦を下げるための patch release とする。

主な対象:

- documentation status の整理
- release tooling の改善
- packaging metadata の確認
- clean install / smoke test 手順の整理
- public API regression の補強

### Release 0.2.0: Engine Capability

`0.2.0` は、downstream package がより自然に Astars を使えるようにするための minor release とする。

候補:

- query / traversal の整理
- source model / source mapping の安定化
- extension-level contract の文書化
- public node interface の強化
- edit primitive の設計 spike
- downstream prototype による検証

### Phase 1: Engine Surface を安定させる

- public API を定義する
- `AParser` のような legacy name を compatibility shim として残すか判断する
- runtime dependency が正しく install されるように package metadata を整える
- README と examples を新 API に合わせる
- clean environment で basic parse/query workflow が動くようにする
- `astars-engine` への repository/package migration plan を決める

### Phase 2: Core Model を安定させる

- `RawSyntaxNode`, CST, AST, `SyntaxGraph` の役割を明確にする
- CST を public API とするか、主に internal/debugging support とするか判断する
- 複数の child selector が同じ attribute を対象にする場合の rule semantics を直す
- source span mapping と AST construction の test を追加する

### Phase 3: Engine Operations を定義する

- traversal primitive を追加する
- query primitive を追加する
- source extraction primitive を追加する
- generic edit/transform primitive を追加する
- domain-specific analysis strategy は core に入れない

### Phase 4: Ecosystem に備える

- `astars` と `astars-*` package の境界を文書化する
- downstream analysis module 向けの extension point を定義する
- 最小の downstream example package または example project を作る
- application-specific dependency を engine に追加しない

### Phase 5: Language Expansion に備える

- language adapter contract を文書化する
- AST rule contract を文書化する
- Java などを second-language validation target として扱う
- Python reference path が安定する前に広い multi-language support を約束しない


## 成功 / 失敗シグナル

Astars が正しい方向に進んでいるかは、実装量ではなく、downstream package が core engine をどれだけ自然に再利用できるかで判断する。

### Success Signals

Astars が正しい方向に進んでいる状態とは、downstream analysis module が次を実現できる状態である。

1. Astars を library として import できる
2. source file を parse できる
3. 安定した AST-like structure を inspect できる
4. analysis result を source span に戻せる
5. generic source-aware operation を実行できる
6. parser 固有の node API に直接依存しなくてよい
7. unrelated な `astars-*` package から独立して使える

追加の成功シグナル:

- downstream package が parser adapter を直接 import しなくなる
- source span 付き finding を簡単に出せる
- 複数の downstream tool が同じ parsed structure を共有できる
- 新しい use case が core 変更なしに実装できる
- core に重い application-specific dependency が増えない

### Non-Success Signals

Astars は、次の状態になり始めたらスコープから外れつつある。

- core に metrics definition、review policy、pruning policy が入り始める
- downstream package が private module や parser-specific object に依存し始める
- source mapping が後付けの optional feature になっている
- public API が内部実装をそのまま露出しすぎている
- core が visualization、reporting、CI workflow まで抱え始める
- `astars` が `astars-*` package をまとめて install する umbrella package になり始める

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

version ごとの release scope は [NEXT_RELEASE_PLAN.ja.md](NEXT_RELEASE_PLAN.ja.md)、直近の action item は [ACTION_ITEMS.ja.md](ACTION_ITEMS.ja.md) を参照する。

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

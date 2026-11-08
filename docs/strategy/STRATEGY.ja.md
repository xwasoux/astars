# Astars 戦略

ステータス: 戦略再構成中

現時点では日本語版を primary document とする。英語版は、戦略文書群が安定してから同期する。

この文書は、Astars をなぜ作るのか、何を中核に置くのか、何を Astars core の外へ置くのかを定義する。個別 API やデータ構造は `design/`、実装と実証の順序は [ROADMAP.ja.md](ROADMAP.ja.md)、具体的な利用シナリオは [USE_CASES.ja.md](USE_CASES.ja.md) で扱う。

## ビジョン

Astars は、プログラムを表層文字列ではなく、構造を持つ状態として扱うための program structure manipulation engine である。

Astars は source code を parse して木を返すだけではない。source、program structure、structural edit、編集前後の対応、variant の派生関係を一つの workflow で扱い、構造に基づく編集と、その結果の分析を可能にする。

短く言えば、Astars は次を目指す。

> プログラムを構造として選択・変形し、その変形過程と結果を、source および元構造との関係を失わず観測できるようにする。

最終的に扱う対象は、コンパイル可能な完成済みプログラムだけではない。構造的編集によって生じる、構文不完全・コンパイル不能な途中状態も対象に含める。途中状態を単なる parse failure として捨てず、どの構造にどの操作を適用して生じたかを保持する。

## 原点と問題意識

Astars の原点は、テキストの挿入・削除を表層文字列だけの問題として扱わず、構文木やグラフ上の操作として分析したいという研究上の要求にある。

文字列 diff や search/replace は実用上重要だが、次の情報を十分には表現しない。

- どの構文要素が編集対象だったか
- 挿入・削除・置換・移動が、構造上どのような操作だったか
- 編集後の node が編集前のどの node から派生したか
- コンパイル不能な途中状態で、何が欠落し、何をしようとしていたか
- 複数の variant が、どの操作系列によって生成されたか

一方、通常の AST は構文的に妥当な完成済みプログラムを表現することに最適化されており、編集中の不完全状態や削除された要素の由来をそのまま保持できるとは限らない。

Astars はこの間を埋める。source text と syntax tree の対応を基礎にしつつ、編集操作と派生関係を first-class data へ段階的に引き上げる。

## 戦略仮説

Astars の価値は、個別機能の新規性ではなく、次の四つを一つの小さな engine model として接続する点にある。

1. **Program Structure**: parser 固有 object から隔離された、操作可能なプログラム構造
2. **Source Mapping**: structure と元 source の対応
3. **Structural Edit**: structure を対象とする編集操作と、その source への反映
4. **Provenance / Lineage**: 編集前後の対応、削除された要素、variant の派生関係

この組み合わせにより、次の loop を成立させる。

```text
構造として観測する
  -> 構造を基準に編集する
  -> 新しい program state を得る
  -> 元の state との関係を保ったまま再び観測・評価する
```

parse/query/edit/diff は独立した機能一覧ではなく、この loop を構成する primitive である。

## 中心モデル

### Program State

Astars が扱う中心単位は、最終的には単独の `SyntaxTree` ではなく program state である。program state は概念的に次を含む。

- source representation
- structural representation
- source と structure の mapping
- validity / diagnostics
- state の由来

現在の実装がこの型をそのまま持つという意味ではない。将来の API と設計を評価するための概念モデルである。

### Structural Edit Operation

編集は一時的な副作用ではなく、保存・検証・再生・比較できる値として扱う方向を目指す。

候補となる操作には、Insert、Delete、Replace/Update、Move、Copy/Graft、Subtree Pruning、操作の合成がある。どの操作を core primitive として確定するかは、各段階の実証後に決める。

### Variant / Provenance Graph

複数の program state と edit operation の関係を graph として追跡する。

- 累積的に編集する sequential variant
- 同じ origin から独立に生成する variant
- subtree 単位の派生
- 編集前後の node 対応
- 削除・置換された node の provenance

系譜追跡は補助 metadata ではなく、最終像の中心機能である。ただし、現在の stage で未実装であることと、戦略上重要であることは分けて扱う。

## 不完全な program state の扱い

Astars は、構文不完全な状態を core の対象に含める。ただし、由来の分からない任意の壊れた文字列について編集意図を推測しない。

区別するのは次の二つである。

1. **Astars が把握する structural edit から派生した不完全状態**
   - 適用した操作、元 node、欠落した要素との関係を保持する
   - parse recovery の結果だけに依存せず、編集意図を provenance から説明できる状態を目指す
2. **外部から単独で与えられた不正 source**
   - parser が回復できた structure、source span、diagnostics を提供する
   - 不明な編集意図を Astars が捏造しない

過去の研究で用いた Extended AST や削除 placeholder は、この要求を満たす先行設計である。Astars が同じ表現を採用するか、operation log と graph mapping で実現するかは未決定とする。

## 想定利用者と優先順位

### Primary: 構造的 program transformation を行う研究者

program reduction、mutation、code similarity、edit-distance learning、code model evaluation などを行う研究者を最初の利用者とする。

この利用者が必要とするのは、単なる parser wrapper ではない。構造を基準に variant を生成し、source へ反映し、編集系列と派生関係を保持し、評価ロジックを自由に組み合わせられる substrate である。

### Secondary Validation: LLM coding agent / framework 作者

LLM に全文転記や行番号ベース diff だけを要求せず、名前・kind・関係で対象を指定させ、編集を適用・再検証したい tool 作者を第二の利用者とする。

LLM agent は Astars の起源ではないが、structure-addressed edit と incomplete state handling が実務でも価値を持つかを検証する重要な用途である。Astars 自体は coding agent product にはならない。

### Supporting Users

次は engine の発展に伴って現れる利用者であり、初期戦略の主語にはしない。

- downstream package author
- repository mining / metrics / review tool の作者
- language adapter contributor
- visualization tool の作者

「Astars を使う package を作る人」を循環的な唯一の顧客像にしない。まず具体的な研究 workflow と LLM editing workflow で必要性を実証する。

## Core の責務

Astars core は次に責任を持つ。

### Parse and Recover

- source を parse する
- parser recovery から得られる structure と diagnostics を保持する
- parser 固有 API を adapter 内へ隔離する

### Represent and Map

- Astars-owned な node / structure を提供する
- node、source bytes、span、parent/child、field の対応を保持する
- 将来は valid tree だけでなく、編集由来の incomplete state を表現する

### Query and Address

- traverse、kind、field、source position 等で node を解決する
- 編集対象を byte offset だけに依存せず指定できる primitive を提供する
- selector policy や曖昧性解消の責任範囲は実証を通じて定める

### Apply and Record Structural Edits

- node を基準に source-aware edit を適用する
- edit operation を記録・検証・再生できる方向へ進化させる
- 編集後の program state と diagnostics を返す

### Track Correspondence and Lineage

- 編集前後の node / source / operation の対応を保持する
- cumulative edit と independent variant を区別する
- 削除された node を単に情報消失させない model を持つ

## Core が所有しないもの

Astars は program state と operation を表現するが、その価値判断は行わない。

- どの node を pruning すべきか
- mutation が良いか悪いか
- code similarity metric の定義
- LLM / CodeBERT 等の model score
- benchmark / dataset の定義
- review comment を出すべきか
- migration recipe
- 型解決、data-flow、taint analysis 等の complete semantic analysis
- 編集後 program の意味的正しさやコンパイル成功の保証
- visualization、reporting、CI product

これらは downstream research code、package、agent、外部 tool の責務とする。

## 既存ツールに対する位置づけ

Astars は parser、diff tool、refactoring framework、static analysis platform の代替を一括して目指すものではない。

- tree-sitter 等の parser infrastructure は、高速で堅牢な syntax tree を提供する。Astars はその上で、source mapping、edit operation、variant lineage を所有する
- GumTree 等の structural diff は、独立した二つの tree 間の対応と edit script を求める。Astars はそれに加えて、既知の operation から派生する途中 state と lineage を扱う
- LibCST や言語固有 AST framework は、特定言語で深い構文操作を提供する。Astars は深さで競争せず、研究・agent workflow が共有できる engine model と parser isolation を重視する
- codemod / refactoring framework は、妥当な最終 source と transformation recipe を重視する。Astars は recipe を所有せず、不完全な途中状態も含めて operation と結果を観測可能にする
- static analysis platform は query、semantic analysis、finding、reporting を含むことがある。Astars は分析判断を持たず、その下で再利用できる program state substrate に留まる

AST editing、tree query、source generation の個別機能だけを独自性として主張しない。Astars の差分は、source-faithful な structure、first-class edit、incomplete state、provenance を、小さな analysis-neutral engine として接続する点に置く。

## Design Principles

### Structure-First, Not Text-Only

source text を捨てないが、操作の意味を byte range だけに還元しない。対象、操作、派生関係を program structure 上で説明できることを目指す。

### Source-Faithful

node から source span / source slice へ戻れることを core value とする。source mapping は optional feature にしない。

### Edit- and Provenance-Faithful

現在の状態だけでなく、どの元構造にどの操作を適用して生じたかを保持する。削除された要素も、必要な範囲で由来を追跡できるようにする。

### Incomplete States Are Data

構文不完全・コンパイル不能な途中状態を、常に failure として捨てない。編集由来の incomplete state は研究・agent workflow の観測対象である。

### Parser-Isolated

初期実装では tree-sitter を使うが、public workflow を tree-sitter object に直接依存させない。parser recovery と Astars の edit provenance も混同しない。

### Analysis-Neutral

Astars は structure、mapping、operation、lineage を提供する。研究仮説、分析 policy、評価関数は core に埋め込まない。

### Small, Composable, Reliable

機能数ではなく、少数の primitive を組み合わせて end-to-end workflow が成立することを優先する。新しい API は、具体的な workflow を止めていることが確認されてから追加する。

### Staged Evolution

最終像を graph-native transformation に置きつつ、そこへ一度に飛ばない。各 stage を独立して利用・検証可能にし、次段階の設計を実例から導く。

### Python Reference Path, Language-Extensible Core

最初は Python を対象言語の reference path とする。他言語対応は、Python 上で operation と lineage model が成立した後、architecture の一般性を検証する目的で行う。

### Rust Core, Binding Consumers

core engine は Rust に置き、Python / Node は binding consumer とする。研究用途では Python、agent 統合では Node が主な入口になり得るが、core logic を重複させない。

## 現在地と最終像

現在の Rust 実装は、tree-sitter CST をほぼ 1:1 で arena に写し、node を source span の address として使う stage にある。`replace` は structure-addressed text edit であり、tree-native edit ではない。

これは最終像ではないが、捨てるべき実装でもない。parse、source mapping、node addressing、再 parse、diagnostics は、後続 stage の実行基盤になる。

最終像では、次を扱う。

- structural edit operation を値として表現する
- subtree の挿入・削除・移動・移植を扱う
- operation sequence を合成・保存・再生する
- valid / incomplete state を同じ lineage 上で扱う
- program variants を graph として追跡する
- source を program state から得られる表現の一つとして扱う

段階の詳細と実証条件は [ROADMAP.ja.md](ROADMAP.ja.md) に定める。

## Ecosystem と配布

`astars` は軽量な core engine の名前とする。pruning、LLM evaluation、metrics、review、visualization 等は必要に応じて downstream package / research project として分離する。

- core は downstream policy に依存しない
- downstream は stable な core primitive に依存する
- umbrella package を先に作らない
- consumer が存在しない interface や package を構想だけで増やさない

repository 名、PyPI / npm 上の最終 package 名は、戦略と public API が安定してから再評価する。rename 自体を価値としない。

## Trade-offs

- 最初から完全な semantic model を持たない
- 最初から全言語を対象にしない
- 最初から lossless pretty-printer を約束しない
- arbitrary malformed source の編集意図を推測しない
- 研究用の全アルゴリズムを core に取り込まない
- 最終像のために現在の小さな API を過剰一般化しない

## Open Questions

- current CST、将来の normalized AST、edit graph を public model 上でどう分離するか
- incomplete state を placeholder node、operation overlay、別 graph のどれで表現するか
- node identity を単一 tree、edit 前後、variant lineage の各範囲でどう定義するか
- source projection 時に comment、whitespace、formatting をどこまで保持するか
- structural operation の最小集合を何にするか
- operation log と program state の serialization format をいつ安定化するか
- second language をどの stage で導入し、何をもって language-extensible と判定するか

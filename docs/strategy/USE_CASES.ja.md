# Astars ユースケース

ステータス: ユースケース draft

関連戦略: [STRATEGY.ja.md](STRATEGY.ja.md)

この文書は、Astars の価値を research use cases と practical engineering use cases に分けて整理する。

Astars の戦略的な価値は、ユースケースごとに見るとより明確になる。ここでは大きく Research Use Cases と Practical Engineering Use Cases に分ける。

## Research Use Cases

研究用途では、柔軟な program structure、正確な source mapping、そして experiment-specific な analysis logic を engine の外で定義できる自由度が重要になる。

### Research Pruning / Program Reduction

Downstream package: `astars-pruning`

研究 workflow では、tree node と source text の対応を保ったまま、program の一部を削除、置換、最小化したいことがある。

Astars がある場合、pruning package は次を行える。

- pruning strategy を core の外で選べる
- generic source-aware edit primitive を使える
- 各 edit を選択された node に追跡できる
- 同じ source mapping model を使って reduced program を比較できる

Astars は pruning policy を所有しない。node-to-source edit substrate を提供する。

### LLM / Code Model Evaluation

Downstream package: `astars-llm-eval`

evaluation dataset では、structural slicing、prompt construction、answer checking、source-region selection などが必要になることがある。

Astars がある場合、evaluation package は次を行える。

- function、class、block、expression を一貫して抽出できる
- dataset provenance のために source span を保持できる
- parser glue を再実装せずに structural variant を作れる
- generated code を source-mapped structure と比較できる

Astars は model score や benchmark を定義しない。それらの workflow に信頼できる program structure を提供する。

### Repository Mining / Software Engineering Research

Downstream package: research scripts または `astars-research-*` packages

ソフトウェア工学研究では、多数の repository を処理し、比較可能な program structure を抽出し、source file への link を保持したいことが多い。

Astars がある場合、research workflow は次を行える。

- 共通の engine surface を通じて repository を parse できる
- function、class、import、statement を一貫して抽出できる
- 再現性のために source span を記録できる
- experiment ごとに parser glue を作り直さなくてよい

Astars は research question を定義しない。structural data collection を信頼しやすくする。

### Language Support Experiments

Downstream または extension package: language adapter package / experimental language support

言語を追加する際の中心課題は、各 downstream package が新しい parser API を学ぶことではなく、その言語を Astars の engine concepts にどう対応させるかである。

Astars がある場合、language support は次を行える。

- parser-specific behavior を adapter に閉じ込められる
- source mapping と query primitive を再利用できる
- core engine shape が Python 以外でも成立するか検証できる
- downstream package が追加言語を段階的に採用できる

Astars は、reference path が安定する前に広い language coverage を約束しない。代わりに、language expansion のための明確な道筋を提供する。

## Practical Engineering Use Cases

実務では、Astars は社内の code understanding、review、migration、governance、LLM-assisted development tool のための共通 engine として使える。

### Metrics / Structural Statistics

Downstream package: `astars-metrics`

Astars がない場合、metrics package は source の parse、node normalization、tree traversal、finding と source location の対応づけを自前で決める必要がある。

Astars がある場合、metrics package は metric definition に集中できる。

- 安定した node interface を通じて function、class、branch、expression を数えられる
- metric location を source span として report できる
- parser-specific node API への直接依存を避けられる
- 他の `astars-*` package と同じ parse/query workflow を再利用できる

Astars は metric を定義しない。metric を計算するための構造を提供する。

### Code Review / Quality Signals

Downstream package: `astars-code-review`

review-oriented tool では、source region を特定し、finding を説明し、正確な line や span に comment を紐づける必要がある。

Astars がある場合、review package は次を行える。

- node から source span に finding を戻せる
- pull request の structural change を要約できる
- parser setup を自前で持たずに review comment を作れる
- structural query と repository-specific policy を組み合わせられる
- review decision を engine の外に保てる

Astars は、ある pattern に review comment を出すべきか判断しない。downstream package が relevant code を特定し説明しやすくする。

### Migration / Refactoring Support

Downstream package: internal migration tools または `astars-migrate`

開発チームでは、deprecated API の検出、framework usage の更新、semi-automatic code modernization などが必要になることがある。

Astars がある場合、migration package は次を行える。

- structural query を通じて古い API call を検出できる
- replacement を正確な source span に対応づけられる
- generic transformation primitive で edit plan を作れる
- migration recipe を engine の外に保てる

Astars は migration recipe を所有しない。recipe package が使える source-aware structure と edit を提供する。

### Architecture / Dependency Rule Checks

Downstream package: internal governance tools

大規模 repository では、layer boundary、forbidden import、team-specific dependency rule の検査が必要になることがある。

Astars がある場合、governance package は次を行える。

- import、class definition、call site を構造的に inspect できる
- violation を source span に紐づけて report できる
- code structure と repository ownership metadata を組み合わせられる
- organization-specific policy を engine の外に保てる

Astars は architecture policy を定義しない。policy package が評価できる structural fact を提供する。

### LLM Coding Assistant Context

Downstream package: internal assistant tooling または `astars-llm-context`

LLM coding workflow では、ファイル全体ではなく、function、class、import、近傍の structural region に基づいて context を取り出したいことがある。

Astars がある場合、assistant package は次を行える。

- mapped program structure に基づいて source を slice できる
- prompt context の provenance を保持できる
- 関連する function や class を一貫して取得できる
- generated code を同じ engine surface で inspect できる

Astars は assistant そのものではない。assistant tool のための source-faithful structure を提供する。

### Test Impact / Change Summaries

Downstream package: CI tooling または repository automation

開発チームでは、pull request でどの function、class、public interface が変わったかを把握したいことがある。

Astars がある場合、automation は次を行える。

- file diff を changed program node に対応づけられる
- structural change summary を生成できる
- downstream heuristic を使って関連 test を提案できる
- summary や finding を正確な source span に紐づけられる

Astars はどの test を必ず実行するべきか判断しない。CI tool が利用できる structural change data を提供する。

### Visualization / Exploration

Downstream package: `astars-visualizer`

visualization tool は structure、label、source position を必要とするが、parser integration を自前で持つ必要はない。

Astars がある場合、visualizer は次を行える。

- 安定した node interface を通じて AST-like structure を描画できる
- 選択された node に対応する source range を highlight できる
- source、syntax node、AST node の mapping を可視化できる
- analysis-specific package から独立したまま実装できる

Astars は visualization product にならない。visualization を可能にする data model を提供する。

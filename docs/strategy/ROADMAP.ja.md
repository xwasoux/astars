# Astars ロードマップ

ステータス: 戦略再構成中

関連文書:

- [STRATEGY.ja.md](STRATEGY.ja.md): Astars の目的、中心モデル、境界
- [USE_CASES.ja.md](USE_CASES.ja.md): 各 stage を検証する具体的 workflow
- [../ACTION_ITEMS.ja.md](../ACTION_ITEMS.ja.md): 現在の短期作業
- [../release/NEXT_RELEASE.ja.md](../release/NEXT_RELEASE.ja.md): 次回releaseのscopeとgate

この文書は、最終像へ向けて何をどの順番で実装・実証するかを定義する。機能一覧を埋める計画ではない。各 stage は、具体的な workflow が成立した証拠を得てから次へ進む。

## 進め方の原則

### Capability より Workflow

「API を実装した」だけでは stage 完了としない。primary use case の一連の流れで使え、次の設計判断に必要な観測が得られたことを完了条件とする。

### 最終像を固定し、実装方式は段階的に決める

最終像は graph-native transformation と variant lineage である。一方、Extended AST、placeholder node、operation overlay、printer 等の具体方式は、必要になる前に固定しない。

### 現在の実装を土台として使う

現在の structure-addressed text edit を捨てて最終像を作り直すのではない。parse、source mapping、node addressing、re-parse、diagnostics を後続 stage の execution substrate として育てる。

### Consumer のない interface を増やさない

CLI、selector DSL、service、追加 binding、追加言語は、primary / secondary workflow が要求した時点で検討する。

## Stage 1: Parse and Source Mapping

### 目的

source を parse し、parser 固有 object に直接依存せず、node と source の対応を観測できるようにする。

### Capability

- parse string / bytes / file
- parent / children / walk
- kind / field による query
- node と byte span / source slice の対応
- source position から node の解決
- parser diagnostics

### 現在地

Rust core と Python / Node binding に基本 capability を実装済み。ただし、現行 `SyntaxTree` は tree-sitter CST の 1:1 arena 表現であり、normalized AST ではない。

### Evidence Gate

- Python source を end-to-end で parse / inspect できる
- node と source span が往復する
- syntax error を diagnostics として観測できる
- binding が parser-specific object を公開しない

この gate は概ね通過済み。今後の reliability issue は stage 横断で修正する。

## Stage 2: Structure-Addressed Source Edit

### 目的

program structure を編集対象の address として使い、一回の source edit を適用し、結果を再び観測する loop を成立させる。

### Capability

- kind / field / name 相当の情報で target 候補を絞る
- node の source span を replace / delete する
- 編集後 source を再 parse する
- diagnostics と changed range を返す
- 編集前の node が直接変更範囲と重なるか問い合わせる

### 現在地

`replace`、`child_by_field_name`、`unchanged_in`、`diff_with` 等を実装済み。これは tree-native edit ではなく、node-addressed text splice である。

現行の `unchanged` は node identity や構造同一性ではなく byte-range overlap の判定である。最終的な provenance model と混同しない。

### Reference Workflow

Python source に対して次を行う小さな research example を作る。

1. statement / expression / subtree 候補を列挙する
2. node 単位の delete / replace variant を生成する
3. 各結果を再 parse し、source と diagnostics を収集する
4. valid / incomplete の両結果を捨てずに列挙する

この段階では完全な lineage model を作らず、次 stage に必要な operation data を観測する。

### Evidence Gate

- byte offset を手書きせず node から一回の編集を適用できる
- valid / invalid の両結果を取得できる
- 編集対象外の source が意図せず書き換わらないことを検証できる
- Python / Node の少なくとも一方の実ランタイムで reference workflow が自動テストされる
- 不正 NodeId / offset、deep tree、FFI error 等が process abort ではなく制御された結果になる

この gate は一部のみ通過している。現在はここを実証・堅牢化する段階である。

## Stage 3: First-Class Structural Edit Operations

### 目的

編集を `replace()` 呼び出しの副作用ではなく、保存・検証・適用・再生できる値にする。

### Capability 候補

- operation kind
- structural target / address
- source projection に必要な payload
- origin state
- before / after mapping
- validation result
- serialization

最小 operation 集合は実証から決める。最初から Insert/Delete/Update/Move の完全な algebra を約束しない。

### Reference Workflow

Stage 2 と同じ variant generation を、operation object の列として記録し、同じ origin に再適用して同一結果を再現する。

### Evidence Gate

- operation を保存して replay できる
- target が存在しない・曖昧・別 state 由来の場合に検出できる
- operation と結果 state / diagnostics を対応づけられる
- source patch と structural intent を区別して表現できる
- research workflow と LLM tool workflow が同じ operation model を使える

## Stage 4: Variant and Lineage Model

### 目的

program state と edit operation の派生関係を graph として保持し、累積 variant と独立 variant を扱う。

### Capability

- state identity
- parent / origin relation
- operation sequence
- old/new node correspondence
- deleted / replaced node provenance
- sequential edit と independent branch
- lineage export

### Reference Workflow

[USE_CASES.ja.md](USE_CASES.ja.md) の Sequential Pruning と Independent Subtree Variants を実装する。

### Evidence Gate

- variant から origin と operation sequence を辿れる
- origin node から各 variant での状態を問い合わせられる
- 削除された node の由来を失わない
- cumulative edit と origin-based subtree variant を同じ model で区別できる
- downstream 評価値を各 state に関連づけられるが、評価関数自体は core に入らない

## Stage 5: Graph-Native Transformation and Incomplete States

### 目的

program graph 自体に対する操作を行い、valid / incomplete state、subtree transformation、operation composition を共通 model で扱う。

### Capability 候補

- subtree insert / delete / update / move / graft
- node builder または structural payload
- parent/child constraint validation
- incomplete node / edge / placeholder の表現
- source projection / regeneration
- operation composition と normalization
- independent tree 間の structural matching

### Reference Workflow

- token に近い細粒度から subtree まで複数粒度で pruning する
- syntax-invalid な途中 state を edit intent 付きで保持する
- operation graph から source 表現を得る
- variant dataset と operation sequence を export する
- LLM が structural operation plan を出力し、同じ engine で適用・検査する

### Evidence Gate

- incomplete state を parser error node だけに還元せず表現できる
- source が不完全でも、欠落した構造と origin を説明できる
- subtree operation を byte span の手計算なしで適用できる
- operation sequence を合成・再生して同じ state を得られる
- primary research workflow と secondary LLM workflow の両方が同じ graph model 上で成立する

## Stage 横断の品質要件

次は特定 stage の後回しにしない。

- untrusted source や深い tree で process abort しない
- public ID / offset / operation input を検証する
- Python / Node の実ランタイムテストを持つ
- source bytes と座標系の規約を固定する
- operation / state の Debug・export 表現を用意する
- docs、generated binding、package artifact の整合性を自動検査する
- benchmark は実際の research workflow の規模から作る

## Language Expansion

second language は独立した最終 stage ではなく、model の一般性を検証する cross-cutting milestone とする。

導入時期は、少なくとも Stage 3 の operation model が Python で実証された後とする。早すぎる多言語化は、未検証 abstraction を固定してしまう。一方、Stage 5 完了まで待つと Python 固有設計が固まりすぎるため、Stage 3 または Stage 4 の節目で一言語を選び、次を検証する。

- node kind / field abstraction
- source mapping
- operation target
- incomplete state representation
- source projection

## Interface Strategy

### Python

Primary research workflow の最初の入口とする。

### Node

Secondary の LLM agent integration を検証する入口とする。Python と別の core semantics を持たせない。

### CLI / Shell

現時点では未確定。operation/state serialization が Stage 3 以降で形になり、具体的な agent workflow が shell interface を要求した場合に検討する。

### Selector DSL

現時点では未確定。実際の target resolution で複合条件と曖昧性処理が繰り返し必要になった場合に設計する。

## 直近の戦略作業

1. `STRATEGY` / `USE_CASES` / `ROADMAP` の用語を design docs と同期する
2. Stage 2 の research reference workflow を具体的な Python example / test として定義する
3. reference workflow で現在の API が漏らす parser glue、byte manipulation、失われる provenance を記録する
4. その観測を基に Stage 3 の operation model を設計する
5. 実装前に Stage 3 の Evidence Gate と最小 serialization example を文書化する

## Success Signals

- source、structure、operation、lineage が同じ workflow で結びつく
- incomplete state を失敗として捨てず研究データにできる
- downstream が parser 固有 object や手書き byte offset に依存しない
- operation を保存・再生し、variant 生成を再現できる
- research と LLM editing が同じ primitive を共有する
- 新しい use case が core 変更なし、または小さな composable primitive の追加で成立する

## Non-Success Signals

- API 数や対応言語数が進捗指標になる
- source mapping だけを持つ tree-sitter wrapper で止まる
- edit operation が使い捨ての text patch のまま残る
- incomplete state をすべて parse failure として捨てる
- research 用と LLM 用で別々の edit model を作る
- consumer のない CLI、DSL、package を先に増やす
- pruning policy、model score、review policy が core へ入る

# Astars Design Documents

ステータス: 再構成中

このディレクトリは、Astars の戦略を実現するための target design、不変条件、設計判断を管理する。

Astars の目的・利用者・優先順位は [../strategy/STRATEGY.ja.md](../strategy/STRATEGY.ja.md)、実装と実証の段階は [../strategy/ROADMAP.ja.md](../strategy/ROADMAP.ja.md)、具体的な workflow は [../strategy/USE_CASES.ja.md](../strategy/USE_CASES.ja.md) を参照する。

## 文書の分割方針

design 文書は、実装時に発生した作業単位ではなく、Astars が所有する design model ごとに分割する。

```text
Strategy
  -> Program Model
      -> Source Model
      -> Operation Model
      -> Provenance Model
  -> Architecture
      -> crates / modules / bindings
```

- model 文書は、実装方式が変わっても維持すべき概念、意味論、不変条件を扱う
- architecture 文書は、各 model を crate / module / binding へどう配置するかを扱う
- ADR は、ある選択を採用した理由、代替案、結果を扱う
- action item や release 文書は、現在の進捗や作業順を扱う

## 読む順序

設計全体を理解する場合は、次の順序で読む。

1. [PROGRAM_MODEL.ja.md](PROGRAM_MODEL.ja.md)
2. [SOURCE_MODEL.ja.md](SOURCE_MODEL.ja.md)
3. [OPERATION_MODEL.ja.md](OPERATION_MODEL.ja.md)
4. [PROVENANCE_MODEL.ja.md](PROVENANCE_MODEL.ja.md)
5. [ARCHITECTURE.ja.md](ARCHITECTURE.ja.md)
6. 必要な [decisions/](decisions/) の ADR

## 文書一覧

### `PROGRAM_MODEL.ja.md`

Astars が program をどのような state / structure として扱うかを定義する中心文書。

主な対象:

- Program State
- syntax structure / normalized structure / edit graph の関係
- node / edge / parent / child / field
- valid state / incomplete state
- parser recovery と編集由来の欠落情報の違い
- node identity の有効範囲
- placeholder / tombstone / operation overlay の設計候補
- model が満たす不変条件

### `SOURCE_MODEL.ja.md`

source representation と program structure の対応を定義する。

主な対象:

- source bytes / decoded text / encoding
- byte span / point / line / column
- newline / invalid UTF-8
- node と source slice の mapping
- comment / whitespace / trivia
- diagnostics の source location
- source projection / regeneration
- formatting preservation の保証範囲

### `OPERATION_MODEL.ja.md`

program structure に対する operation の意味論と適用規約を定義する。

主な対象:

- structural target / address
- Insert / Delete / Replace / Move / Graft 等の operation 候補
- operation validation
- operation application pipeline
- before / after Program State
- operation result
- replay / composition / serialization の要求
- structure-addressed text edit と graph-native edit の違い

### `PROVENANCE_MODEL.ja.md`

program state、operation、node の派生関係を定義する。

主な対象:

- state / operation identity
- origin / parent / child variant
- sequential edit / independent variant
- node correspondence
- deleted / replaced node の provenance
- operation sequence
- lineage graph
- 既知の operation による lineage と、独立した二木の structural matching の違い

### `ARCHITECTURE.ja.md`

各 design model を実装上の layer、crate、module、binding へ配置する。

主な対象:

- system boundary
- target architecture
- current implementation
- target と current の gap
- dependency direction
- module responsibility
- public / internal boundary
- Rust core と Python / Node binding の関係

個別 operation の意味論、座標系の選択理由、研究 scenario はこの文書へ集約しない。

### `decisions/`

Architecture Decision Record(ADR)を置く。

ADR は次の形式を基本とする。

```markdown
# Decision title

Status: Proposed | Accepted | Superseded

## Context
## Decision
## Consequences
## Alternatives
## Related Documents
```

model 文書には現在有効な規約を書く。なぜその規約を選んだか、どの案を退けたかは ADR に残す。

## 記載先の判断基準

| 内容 | 記載先 |
|---|---|
| なぜ Astars を作るか | `strategy/STRATEGY.ja.md` |
| 誰のどの workflow を改善するか | `strategy/USE_CASES.ja.md` |
| どの順序で実装・実証するか | `strategy/ROADMAP.ja.md` |
| program state / node / incomplete state の意味 | `PROGRAM_MODEL.ja.md` |
| source / span / encoding / projection の意味 | `SOURCE_MODEL.ja.md` |
| operation の意味と適用規約 | `OPERATION_MODEL.ja.md` |
| state / node / operation の派生関係 | `PROVENANCE_MODEL.ja.md` |
| model をどの module が所有するか | `ARCHITECTURE.ja.md` |
| 特定の設計選択とその理由 | `decisions/` |
| 現在の実装状況、次の短期作業 | `ACTION_ITEMS.ja.md` |
| version / publish 単位の計画 | `release/` |

## Target Design と Current Implementation

design 文書では、最終的に必要な model と、現在実装済みの範囲を混同しない。

各 model 文書は、必要に応じて次の節を持つ。

1. **Target Model**: 最終的に満たす意味論と不変条件
2. **Current Stage**: 現行実装が満たす範囲
3. **Known Gaps**: target との差
4. **Open Questions**: 未決定事項

未実装であることは target design から削除する理由にはしない。一方、将来必要かもしれないというだけの機能を target として確定しない。

## 用語の規約

戦略再構成中は、次の用語を区別する。

- **source**: bytes / text としてのソースコード表現
- **syntax structure**: parser が source から生成した構文構造
- **program structure**: Astars が所有し、操作・分析に利用する構造の総称
- **Program State**: source、structure、diagnostics、provenance を含む概念上の状態
- **operation**: Program State または program structure に適用する編集操作
- **variant**: origin state から operation によって派生した Program State
- **incomplete state**: 構造的編集等により構文・コンパイル上不完全になった Program State
- **lineage**: state / operation / node の派生関係

`AST` は文脈によって raw parser tree、normalized tree、編集可能 graph を指し得るため、model が確定するまでは単独で曖昧に使わない。必要に応じて `tree-sitter CST`、`normalized AST`、`program graph` のように対象を明示する。

## 将来必要になった時点で追加する文書

現時点では作成しない。

- `LANGUAGE_ADAPTER_CONTRACT.ja.md`: second language 導入時
- `PUBLIC_API_MODEL.ja.md`: Program State / Operation を stable API として公開する段階
- `STORAGE_MODEL.ja.md`: lineage graph / dataset の永続形式が必要になった段階

文書名を先に予約するためだけに空の design document を増やさない。

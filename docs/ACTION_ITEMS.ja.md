# Astars Action Items

最終確認日: 2026-11-08

この文書は、作業を再開するときに最初に読むための短期 action item 一覧である。
背景や設計理由は各計画文書に残し、ここでは「次に何をするか」と完了条件だけを管理する。実装の詳細な経緯は `git log` を参照。

関連文書:

- [strategy/STRATEGY.ja.md](strategy/STRATEGY.ja.md) — ビジョン、戦略仮説、coreの責務
- [design/README.md](design/README.md) — design文書の索引と読む順序
- [design/ARCHITECTURE.ja.md](design/ARCHITECTURE.ja.md) — target architectureとcurrent / target gap
- [design/OPERATION_MODEL.ja.md](design/OPERATION_MODEL.ja.md) — operationの意味論と適用規約
- [design/PROVENANCE_MODEL.ja.md](design/PROVENANCE_MODEL.ja.md) — lineageとstructural correspondence
- [release/NEXT_RELEASE.ja.md](release/NEXT_RELEASE.ja.md)
- [design/decisions/](design/decisions/) — 実装上の設計判断と理由
- [release/RELEASE_POLICY.ja.md](release/RELEASE_POLICY.ja.md)
- [release/RELEASE_PROCESS.ja.md](release/RELEASE_PROCESS.ja.md)
- [strategy/ROADMAP.ja.md](strategy/ROADMAP.ja.md)

## 直近の作業順

1. Stage 2の未通過Evidence Gateを埋める
   - [ ] 不正な`NodeId` / offsetをpanicではなく制御されたerrorとして返す
   - [ ] deep treeとFFI境界のfailure testを追加する
   - [ ] node単位のvariant生成reference workflowを自動テストする
2. 次回releaseのscopeを決める
   - [ ] field navigationとindependent diffを同じreleaseへ含めるか決定する
   - [ ] `EditResult`をknown editとinferred diffで共有するかpublic API reviewする
   - [ ] target versionを確定し、`NEXT_RELEASE`を`Planned`へ進める
3. Stage 3の設計へ進む条件を確認する
   - [ ] reference workflowから最小Operation dataを抽出する
   - [ ] research workflowとLLM tool workflowで同じOperation Modelを使えるか検証する

順序とstageの完了条件は[ROADMAP.ja.md](strategy/ROADMAP.ja.md)、release固有の判断は[NEXT_RELEASE.ja.md](release/NEXT_RELEASE.ja.md)を正とする。

## Current Baseline

Rust core(`crates/astars-core`)+ Python/Node binding(`bindings/python`、`bindings/node`)で、以下を実装・動作確認済み(Python/Node 両方で実機確認)。設計の詳細は[design/ARCHITECTURE.ja.md](design/ARCHITECTURE.ja.md)、編集方式の判断は[ADR 0002](design/decisions/0002-stage-2-source-splice-and-incremental-reparse.ja.md)を参照。

- monorepo 構成(`crates/astars-core` + `bindings/python` + `bindings/node`)。クラス図は draw.io から Mermaid に移行済み
- parse: `parse_str` / `parse_bytes` / `parse_file`(`parse_file` は WHATWG encoding ラベル対応、`encoding_rs` 使用)
- query: `walk` / `find(kind)` / `node_at(offset)` / `span_of` / `source_of` / `point_at(byte_offset)`(0-based line/column)
- 編集 primitive(v1): `replace(target, new_text)` + `unchanged_in(id, edit)`(`tree.edit()` + `changed_ranges`ベース、ADR 0002参照)
- unreleased: `child_by_field_name`によるfield navigation
- unreleased: `diff_with` / `EditResult::unchanged`によるindependent-source changed-range近似
- diagnostics: parser recovery(`ERROR`/`MISSING` node)の公開
- examples(`examples/python/basic_parse.py` / `examples/node/basic-parse.js`)を上記全機能のデモに更新済み

## Capability Status

`STRATEGY.ja.md`の戦略仮説とDesign Principlesに対して、現在のrepositoryでどこまで実装・実証できているかを4つに分けて追跡する。公開済みversionとの差は`CHANGELOG.md`と`NEXT_RELEASE`を参照する。

### 1. Source-faithful かつ編集可能な構造(parse → query → edit → re-analyze の loop)

現行のquery / operation capabilityを追跡する。意味論は`PROGRAM_MODEL` / `OPERATION_MODEL` / `PROVENANCE_MODEL`を参照。

- [x] structure query: parent/children、walk、find、node_at、span_of、source_of
- [x] structure-addressed edit: `replace`
- [x] changed-range query: `unchanged_in`
- [x] 部分木の一括export: `dump`
- [x] nodeを値としてFFI境界越しに扱える
- [x] field navigation: `child_by_field_name(id, field_name)`。`name`を特別扱いせず、`find(kind) + child_by_field_name + source_of`を組み合わせる。Python/Node両bindingで実機確認済み
- [ ] provenance tracking: variantが元のどのstate / operation / nodeから来たかを追跡する台帳
- [x] independent source diffのStage 2近似: `SyntaxTree::diff_with(new_source) -> EditResult`。line-based changed rangeのみでnode matchingは行わない。意味上の制約は[ADR 0004](design/decisions/0004-independent-source-diff-is-inferred.ja.md)を参照

Stage 2の土台はできている。主な未実装はfirst-class Operation、provenance tracking、structural correspondenceである。

### 2. 複数ランタイムでの再利用性

- [x] Python/Node両bindingが、共有するcore capabilityについてsemantic parityを持つ（runtime制約によるAPI形状の差は許容し、両runtimeで実機確認済み）
- [x] PyPI / npmへの公開（`astars-py` 0.2.0をPyPIへ、`@astars/native` 0.2.0をnpmへpublish済み。公開履歴は`CHANGELOG.md`と`v0.2.0` tagを参照）

### 3. LLMエージェント向けstructure-addressed editing

- [x] `replace` + `unchanged_in` による「編集して暴走していないか確認する」ワークフローの土台
- [x] field-based addressing — 強み1と同じ項目。`child_by_field_name`で実装済み
- [ ] selector DSL(`kind=... AND name=...` のような複合条件を1呼び出しで解決する仕組み。具体的な消費者が出るまで見送り)

### 4. ecosystem 中核としての軽量 engine

- [ ] downstream package の実装例が1つもない(`astars-metrics` 等は `STRATEGY.ja.md` 上の構想のみ)
- [ ] `USE_CASES.ja.md`のreference workflowをエンドツーエンドで動かす実例がない

### その他(強みと直接紐づかないが明示的に見送っているもの)

- stable CST / `RawSyntaxNode` public API
- semantic analysis
- multi-language support(Python 以外の対象言語)
- legacy API compatibility(`AParser`/`APruner`/`ATraverser` 等)

いずれも「具体的な消費者が出てくるまで着手しない」方針のままである。

## Frozen Python Prototype

`prototype-python/`の完了事項は旧Python実装にだけ適用され、現行Rust実装の保証とはみなさない。invalid offsetやforeign nodeを制御されたerrorにする方針は設計上の参照点だが、Rust側ではまだStage 2 Evidence Gateの未完了事項である。過去の作業経緯は`prototype-python/README.md`と`git log`を参照する。

## Update Rule

- 作業を開始した item は、その commit または pull request で checkbox を更新する
- 新しい短期作業はまずこの文書に追加し、詳細設計が必要なら専用 plan に分ける
- release、branch、実装言語の方針が変わったら`Current Baseline`も更新する
- capabilityに手をつけたら、該当するcheckboxを更新する
- 完了した短期itemは恒久的な履歴として蓄積せず、必要な事実だけをdesign文書・CHANGELOG・Git履歴へ移す

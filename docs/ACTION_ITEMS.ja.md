# Astars Action Items

最終確認日: 2026-10-16

この文書は、作業を再開するときに最初に読むための短期 action item 一覧である。
背景や設計理由は各計画文書に残し、ここでは「次に何をするか」と完了条件だけを管理する。

関連文書:

- [STRATEGY.ja.md](STRATEGY.ja.md)
- [NEXT_RELEASE_PLAN.ja.md](NEXT_RELEASE_PLAN.ja.md)
- [SOURCE_MAPPING_PLAN.ja.md](SOURCE_MAPPING_PLAN.ja.md)
- [RELEASE_STRATEGY.ja.md](RELEASE_STRATEGY.ja.md)
- [ROADMAP.ja.md](ROADMAP.ja.md)

## Current Snapshot

- `STRATEGY.ja.md` で、core engine の実装言語を Rust にする方針を確定した
- Python package と TypeScript package は、Rust core への binding 経由の consumer として位置づける
- この方針変更に伴い、`feature/0.2-source-mapping` 上の Python source mapping 安定化作業は一時停止する
- 現在の Python 実装(`SourceText` 導入まで含む)は、Rust 移行までの prototype / 設計検証として扱う
- `0.1.1` の maintenance release は出さないことを決定した(Rust 移行に集中する)
- repository 構成は単一 repo(monorepo)に決定した。`astars-core`(Rust)、Python binding、Node binding を同一 repository で管理する。比較検討は [architecture/repo-structure.drawio.svg](architecture/repo-structure.drawio.svg) 参照
- `main` の最新 release は `v0.1.0`

## Next Action

次に着手する作業は、Rust 移行の最初のステップを決めることである。

- [ ] monorepo 内のディレクトリ構成を決める(例: `crates/astars-core`、`bindings/python`、`bindings/node`)
- [ ] Rust + tree-sitter + PyO3 の最小 spike を作る(文字列を parse して node 数を返す程度)、toolchain を検証する
- [ ] 同様に napi-rs 経由の Node binding の最小 spike を作る
- [ ] Rust core の v0 scope を文書化する(現 Python `0.1.0` 相当: parse / normalize / map / query を想定)
- [ ] 現在の Python 実装(`feature/0.2-source-mapping` を含む)の扱いを決める(prototype として凍結 / 参照用に残す / archive する)

完了条件:

- Python と Node 両方の binding spike が動作する(parse できて、何らかの値が両言語から取得できる)
- Rust core v0 scope が文書化されている
- 既存 Python 実装の扱いが決まっている

## Decided: Release 0.1.1 は出さない

`0.1.1` は release tooling と documentation の maintenance release として計画していたが、Rust 移行に集中するため出さないことを決定した。`v0.1.0` を Python line の最終 release とする。

## Paused: Python Source Mapping Stabilization (Rust 移行待ち)

以下は `feature/0.2-source-mapping` 上で進めていたが、Rust 移行方針により一時停止する。設計判断そのもの(tie-breaker、boundary 挙動、mapping failure の扱いなど)は Rust core 設計時に再利用する前提で、[SOURCE_MAPPING_PLAN.ja.md](SOURCE_MAPPING_PLAN.ja.md) にそのまま残す。

- `SyntaxGraph.ast_at()` / `SourceUnit.node_at()` の選択規則 test 固定
- mapping failure の扱いの test 化
- Documentation and cleanup 項目
- `0.1.1` release 後の `develop` 取り込みと `0.2.0` 統合

## Decisions Needed

次の判断は Rust 移行を具体的に進める前に行う。

- [ ] monorepo 内のディレクトリ構成(crates / bindings のレイアウト)
- [ ] binding 層(PyO3 / maturin、napi-rs)の設計をいつ着手するか
- [ ] 既存 Python 実装をどの程度の期間、どんな形で残すか

設計レベルで決まっているが実装(Rust)にまだ反映していないもの(Python prototype で検証済み、`SOURCE_MAPPING_PLAN.ja.md` の Resolved Decisions 参照):

- 不連続な raw spans は covering span で表す
- tie-breaker は AST tree 上の具体性を優先する
- 1-based location helper は当面 scope から外す
- `SourceText` 相当の責務は internal model に留める

## Completed on the Python Prototype (`feature/0.2-source-mapping`)

Rust 移行後も設計の参照点として記録を残す。

- [x] source mapping の public behavior を文書化した
- [x] invalid offset を `AstarsError` とする方針を固定した
- [x] foreign `SourceUnit` の node を `AstarsError` とする方針を固定した
- [x] EOF offset で `node_at()` が `None` を返すようにした
- [x] Unicode source の UTF-8 byte offset test を追加した
- [x] non-UTF-8 file input の mapping test を追加した
- [x] zero-width diagnostic span の test を追加した
- [x] `SourceText` internal model を導入した
- [x] `SourceUnit` の validation / slicing / point conversion を `SourceText` に寄せた

## Not Now

次の項目は重要だが、Rust core の v0 scope が固まるまで着手しない。

- edit primitive の本格実装
- selector DSL
- stable CST / `RawSyntaxNode` public API
- semantic analysis
- multi-language support
- legacy API compatibility
- downstream package 本体

## Update Rule

- 作業を開始した item は、その commit または pull request で checkbox を更新する
- 新しい短期作業はまずこの文書に追加し、詳細設計が必要なら専用 plan に分ける
- release、branch、実装言語の方針が変わったら `Current Snapshot` も更新する
- 完了済み item が増えすぎたら、release 単位で `CHANGELOG.md` に移してこの文書を短く保つ

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
- monorepo 内のディレクトリ構成を実行した。`crates/astars-core`(単一 core crate)、`bindings/python`(`astars-py`)、`bindings/node`(`astars-node`)の Cargo workspace を作成し、`cargo build --workspace` / `cargo test --workspace` が通ることを確認済み(現時点は placeholder 実装)
- 既存 Python 実装は `prototype-python/` に退避した(frozen reference。詳細は `prototype-python/README.md`)
- `crates/astars-core` に tree-sitter 依存を追加し、`parse_str(source, lang) -> ParseResult` の最小実装を作った。設計は [architecture/core-parse-spike.drawio.svg](architecture/core-parse-spike.drawio.svg) のクラス図(自然言語 → モデル → コードの順で作成)に対応している。`cargo test -p astars-core` で実際に Python source を parse して node 数を数えるテストが通る。`bindings/python` / `bindings/node` の placeholder もこの実装を呼び出す形に更新済み
- `bindings/python`(crate `astars-py`)に pyo3 + maturin を wiring した。設計は [architecture/python-binding-spike.drawio.svg](architecture/python-binding-spike.drawio.svg) のクラス図に対応している。`astars-core` 自体は pyo3 に依存させず、`PyLang` / `PyParseResult` を変換用のミラー型として `bindings/python` 側に新設する形にした。モジュール名は `_astars`(将来の `import astars` は別パッケージとして薄くラップする想定)。`maturin develop` でビルド・インストールし、実際に Python から `_astars.parse_str(source, _astars.PyLang.Python)` を呼んで node_count が取れることを確認済み。`cargo test -p astars-py` も通る(pyo3 の `extension-module` feature は Cargo.toml のデフォルトではなく、`pyproject.toml` の `[tool.maturin] features` 経由でのみ有効化する形にして、`cargo test` のリンクエラーを回避した)
- `main` の最新 release は `v0.1.0`

## Next Action

次に着手する作業は、`bindings/node` に napi-rs wiring を入れることである。

- [x] `crates/astars-core` に tree-sitter 依存を追加し、文字列を parse して node 数を返す最小実装を作る
- [x] `bindings/python`(`astars-py`)に pyo3 + maturin を wiring し、Python から呼び出せる最小 spike を作る
- [ ] `bindings/node`(`astars-node`)に napi-rs を wiring し、Node から呼び出せる最小 spike を作る
- [ ] Rust core の v0 scope を文書化する(現 Python `0.1.0` 相当: parse / normalize / map / query を想定)

完了条件:

- Python と Node 両方の binding spike が動作する(parse できて、何らかの値が両言語から取得できる)
- Rust core v0 scope が文書化されている

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

- [ ] `astars-core` を最初から複数 crate に割るか(現時点では単一 crate の方針)
- [ ] pyproject.toml(maturin)/ package.json(napi-rs)をどのタイミングで `bindings/*` に追加するか(現時点は Cargo crate の skeleton のみ)

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

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
- `bindings/node`(crate `astars-node`)に napi-rs を wiring した。設計は [architecture/node-binding-spike.drawio.svg](architecture/node-binding-spike.drawio.svg) のクラス図に対応している。Python binding と同じ形で、`JsLang` / `JsParseResult` を変換用のミラー型として新設(`JsParseResult` はメソッドを持たないため `#[napi(object)]` の plain object にした)。npm package 名は `@astars/native`。`npm run build:debug` でビルドし、実際に Node から `parseStr(source, JsLang.Python)` を呼んで `nodeCount` が取れることを確認済み(snake_case の `node_count` は napi-rs の規約で自動的に camelCase になる)。pyo3 の時と違い `cargo build` / `cargo test` は素直に通った。`index.js` / `index.d.ts` / `*.node` / `node_modules/` は生成物のため `.gitignore` に追加(`package.json` だけは既存の `*.json` 除外ルールを `!` で上書きして追跡対象にした)
- `docs/ARCHITECTURE.ja.md` を `docs/architecture/ARCHITECTURE.ja.md` に移動し、中身を旧 Python package layout 前提から Rust 構成(`crates/astars-core` + `bindings/*`)向けに書き直した。4枚の draw.io 図(`repo-structure` / `core-parse-spike` / `python-binding-spike` / `node-binding-spike`)への参照と、Rust core の v0 scope(現状の spike と、v0 到達に残っている作業の一覧)を記載済み。他の doc(`README.md`, `V0_PLAN.ja.md`, `SOURCE_MAPPING_PLAN.ja.md`, `MIGRATION.ja.md`, `API_STRATEGY.ja.md`, `DOCS_PLAN.ja.md`)のリンクも新しいパスに修正済み
- AST node 構造の設計に着手する前に、「編集でテキストと木がどう追従するか」を [architecture/EDIT_MODEL.ja.md](architecture/EDIT_MODEL.ja.md) に整理した。要点: (1) 4シナリオ(LLM構造化編集・変異生成パイプライン・embedding・可視化)から操作リストを導出、(2) tree-sitter の `Tree::edit` + `parse_with(..., Some(&old_tree))` + `changed_ranges` に任せられる部分と、テキスト格納(Piece Table 想定)・名前/kindアドレス指定・系譜追跡は自前実装が必要な部分を分担整理、(3) 運用規約として「編集は常に `tree.edit()` 経由で行い独立 re-parse を避ける」を決定
- `main` の最新 release は `v0.1.0`

## Next Action

次に着手する作業は、[architecture/EDIT_MODEL.ja.md](architecture/EDIT_MODEL.ja.md) の Open Questions(AST node の arena 設計、Piece Table の実装方針、系譜追跡の置き場所)を踏まえて、AST node のデータ構造を設計することである。

- [x] `crates/astars-core` に tree-sitter 依存を追加し、文字列を parse して node 数を返す最小実装を作る
- [x] `bindings/python`(`astars-py`)に pyo3 + maturin を wiring し、Python から呼び出せる最小 spike を作る
- [x] `bindings/node`(`astars-node`)に napi-rs を wiring し、Node から呼び出せる最小 spike を作る
- [x] Rust core の v0 scope を文書化する(現 Python `0.1.0` 相当: parse / normalize / map / query を想定)
- [x] 編集時のテキスト/木の追従モデルを整理する(`EDIT_MODEL.ja.md`)
- [ ] AST node のデータ構造を設計する(`EDIT_MODEL.ja.md` の Open Questions を踏まえる)
- [ ] v0 scope の残作業(`SyntaxGraph`、`SourceSpan`/query API)に着手する

完了条件:

- [x] Python と Node 両方の binding spike が動作する(parse できて、何らかの値が両言語から取得できる)
- [x] Rust core v0 scope が文書化されている

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

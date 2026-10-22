# Astars Action Items

最終確認日: 2026-10-22

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
- `crates/astars-core` に tree-sitter 依存を追加し、`parse_str(source, lang) -> ParseResult` の最小実装を作った。設計は `core-parse-spike.drawio.svg` のクラス図(自然言語 → モデル → コードの順で作成)に対応していた(この図は後の `SyntaxTree` 導入で完全に陳腐化したため 2026-10-22 に削除し、現行の設計は [ARCHITECTURE.ja.md](architecture/ARCHITECTURE.ja.md) の Mermaid クラス図に引き継いだ)。`cargo test -p astars-core` で実際に Python source を parse して node 数を数えるテストが通る。`bindings/python` / `bindings/node` の placeholder もこの実装を呼び出す形に更新済み
- `bindings/python`(crate `astars-py`)に pyo3 + maturin を wiring した。設計は `python-binding-spike.drawio.svg` のクラス図に対応していた(後に陳腐化・削除。現行は [ARCHITECTURE.ja.md](architecture/ARCHITECTURE.ja.md) 参照)。`astars-core` 自体は pyo3 に依存させず、`PyLang` / `PyParseResult` を変換用のミラー型として `bindings/python` 側に新設する形にした。モジュール名は `_astars`(将来の `import astars` は別パッケージとして薄くラップする想定)。`maturin develop` でビルド・インストールし、実際に Python から `_astars.parse_str(source, _astars.PyLang.Python)` を呼んで node_count が取れることを確認済み。`cargo test -p astars-py` も通る(pyo3 の `extension-module` feature は Cargo.toml のデフォルトではなく、`pyproject.toml` の `[tool.maturin] features` 経由でのみ有効化する形にして、`cargo test` のリンクエラーを回避した)
- `bindings/node`(crate `astars-node`)に napi-rs を wiring した。設計は `node-binding-spike.drawio.svg` のクラス図に対応していた(後に陳腐化・削除。現行は [ARCHITECTURE.ja.md](architecture/ARCHITECTURE.ja.md) 参照)。Python binding と同じ形で、`JsLang` / `JsParseResult` を変換用のミラー型として新設(`JsParseResult` はメソッドを持たないため `#[napi(object)]` の plain object にした)。npm package 名は `@astars/native`。`npm run build:debug` でビルドし、実際に Node から `parseStr(source, JsLang.Python)` を呼んで `nodeCount` が取れることを確認済み(snake_case の `node_count` は napi-rs の規約で自動的に camelCase になる)。pyo3 の時と違い `cargo build` / `cargo test` は素直に通った。`index.js` / `index.d.ts` / `*.node` / `node_modules/` は生成物のため `.gitignore` に追加(`package.json` だけは既存の `*.json` 除外ルールを `!` で上書きして追跡対象にした)
- `docs/ARCHITECTURE.ja.md` を `docs/architecture/ARCHITECTURE.ja.md` に移動し、中身を旧 Python package layout 前提から Rust 構成(`crates/astars-core` + `bindings/*`)向けに書き直した。4枚の draw.io 図(`repo-structure` / `core-parse-spike` / `python-binding-spike` / `node-binding-spike`)への参照と、Rust core の v0 scope(現状の spike と、v0 到達に残っている作業の一覧)を記載済み。他の doc(`README.md`, `V0_PLAN.ja.md`, `SOURCE_MAPPING_PLAN.ja.md`, `MIGRATION.ja.md`, `API_STRATEGY.ja.md`, `DOCS_PLAN.ja.md`)のリンクも新しいパスに修正済み
- AST node 構造の設計に着手する前に、「編集でテキストと木がどう追従するか」を [architecture/EDIT_MODEL.ja.md](architecture/EDIT_MODEL.ja.md) に整理した。要点: (1) 4シナリオ(LLM構造化編集・変異生成パイプライン・embedding・可視化)から操作リストを導出、(2) tree-sitter の `Tree::edit` + `parse_with(..., Some(&old_tree))` + `changed_ranges` に任せられる部分と、テキスト格納(Piece Table 想定)・名前/kindアドレス指定・系譜追跡は自前実装が必要な部分を分担整理、(3) 運用規約として「編集は常に `tree.edit()` 経由で行い独立 re-parse を避ける」を決定
- `SyntaxTree` / `SyntaxNode` を実装した。設計は `syntax-tree-structure.drawio.svg` のクラス図に対応していた(2026-10-22、Mermaid への移行に伴い削除。現行の設計は [ARCHITECTURE.ja.md](architecture/ARCHITECTURE.ja.md) の「astars-core」クラス図)。`NodeId`(arena index)で node を値として持ち、v0 は 1 raw node = 1 `SyntaxNode`(rule 正規化なし)なので span は node に直接持たせた(`SyntaxGraph` 相当は不要)。`SyntaxTree` は `tree_sitter::Tree` を private field として保持し、将来の incremental edit(`EDIT_MODEL.ja.md`)に備えている。`walk` / `find(kind)` / `node_at(offset)` / `span_of` / `source_of` を実装し、EOF 境界・span/source 往復をテストで確認済み(`cargo test -p astars-core` で7件pass)。設計からの逸脱: `kind`/`field_name` は `&'static str` の予定だったが `tree_sitter::Node::kind()` が実際には tree の lifetime に紐づくため `String` に変更した。`ParseResult.node_count` は `tree: SyntaxTree` に置き換え、`bindings/python` / `bindings/node` は `tree.walk().count()` で計算する形に最小限追従(`SyntaxTree` を binding にどう公開するかは別ラウンド)
- `SyntaxTree` を Python / Node binding に公開した。設計は `python-tree-binding.drawio.svg` / `node-tree-binding.drawio.svg` のクラス図に対応していた(2026-10-22、Mermaid への移行に伴い削除。現行の設計は [ARCHITECTURE.ja.md](architecture/ARCHITECTURE.ja.md) の「bindings/python」/「bindings/node」クラス図)。`astars-core` に `root()` / `kind_of()` / `field_name_of()` / `parent_of()` / `children_of()` という granular accessor を追加し(`NodeId::as_u32`/`from_u32` で FFI 境界を越える)、`PySyntaxTree`/`JsSyntaxTree`(wrapper)と `PyNodeInfo`/`JsNodeInfo`(DTO)を実装。`walk`/`find` は Rust 側の遅延 iterator を binding 層で `Vec` に collect してから返す(node 1個ごとに FFI を跨がない、`EDIT_MODEL.ja.md` 操作11)。`node_info`(1件)と `dump`(部分木一括)を両方用意。Python/Node 両方で実際に動作確認済み(`examples/python/basic_parse.py` / `examples/node/basic-parse.js` で同一結果を再現)。**設計からの逸脱(Node 側のみ)**: 図では `JsParseResult`(`#[napi(object)]`)が `tree: JsSyntaxTree` を持つ想定だったが、napi-rs の `#[napi(object)]` は全 field に双方向変換を要求し `#[napi]` class を直接持てないため、`JsParseResult` を廃止して `lang` を `JsSyntaxTree` 自身の field(getter)に畳み込み、`parseStr()` が `JsSyntaxTree` を直接返す形にした。Python 側は `Py<PySyntaxTree>` でこの問題を素直に解決できたため、Python/Node で非対称な形になっている
- AWS が Kiro IDE 向けに AST ベースの構造化編集(名前/kind セレクタ + insert/replace/delete)を公開し、LLM 呼び出し数・token 数・エラー率で実測効果を示した(2026-10-21、[参考](https://aws.amazon.com/jp/blogs/news/surgical-precision-with-ast/))。シナリオA の仮説の裏付けにはなるが、Kiro は特定 IDE に閉じた内製機能であり、(1) 複数ランタイムでの再利用性、(2) 編集を「結果を解析する loop の一部」として扱う点、は Astars 固有の強みとして残る。これを踏まえ、v0 scope の残作業(`parse_bytes`/`parse_file`/Diagnostics)より**編集 primitive(操作7)+ 編集前後比較(操作8)を Python/Node 両方に公開することを優先する**よう再優先順位付けした。設計方針は [architecture/EDIT_MODEL.ja.md](architecture/EDIT_MODEL.ja.md) の「編集 primitive(v1)の設計」に記載
- 編集 primitive(v1)を Python / Node binding に公開した。`PySyntaxTree`/`JsSyntaxTree` に `replace(target, new_text)` / `unchanged_in(id, edit)` を追加し、`PyEditResult`/`JsEditResult`(`tree` getter)を新設(いずれも `astars_core::EditResult` を丸ごと保持し、`changed_ranges` が private のため `tree` だけに分解できない形)。Python は実装済みの `Py<PySyntaxTree>` パターン、Node は既存の `JsParseResult` 廃止パターンと同じ理由(napi-rs の `#[napi(object)]` が `#[napi]` class field を持てない)で `JsEditResult` も通常の `#[napi]` class にした。両言語で `cargo test` / `clippy -- -D warnings` が通り、`maturin develop` / `npm run build:debug` 後に実際に `x = 1\ny = 2` を `x = 99\ny = 2` に replace して `unchanged_in` の真偽が意図通り(編集対象: false / 無関係な node: true)になることを確認済み
- v0 scope の残作業(`parse_bytes` / `parse_file` / Diagnostics / Unicode・encoding 境界)を実装し、Python / Node 両 binding に公開した。詳細:
  - `astars-core::parse_bytes(source: &[u8], lang)` を追加。`ParseAdapter::parse` が `&str` ではなく `&[u8]` を受け取る形に変更し、`parse_str` はその薄いラッパーにした。`source` は valid UTF-8 でなくてもよい(tree-sitter はバイト列をそのまま parse できる)
  - `astars-core::parse_file(path: &Path, lang) -> Result<ParseResult, AstarsError>` を追加(`AstarsError::Io` のみ)。**設計からの逸脱**: Python prototype の `parse_file(..., encoding=...)` と異なり encoding パラメータは無い。v0 はファイルの bytes をそのまま `parse_bytes` に渡すだけ(UTF-8 前提、lossy)で、非 UTF-8 encoding(Shift-JIS 等)のサポートは "Not Now" に回した(`encoding_rs` のような追加依存を今は入れない判断)
  - `SyntaxTree::source_of` を `&str`(`.expect()` で UTF-8 境界外だと panic)から `String`(`String::from_utf8_lossy(...).into_owned()`)に変更した。`parse_bytes` が非 UTF-8 bytes を受け付けるようになったため、無効な byte 列を読んでも panic せず U+FFFD に置換される(`docs/SOURCE_MAPPING_PLAN.ja.md` の `errors="replace"` 方針を踏襲)。byte offset(`span_of` 等)自体は常に元 bytes 基準のままで、影響を受けるのは `source_of` の表示文字列のみ
  - `astars-core::Diagnostic` { severity: `Severity`(v0 は `Error` 1 variant のみ), message, span: `ByteSpan` } を新設し、`SyntaxTree::diagnostics() -> Vec<Diagnostic>` を実装。tree-sitter の `is_error()` / `is_missing()` node を raw tree から直接 traverse して組み立てる。**設計からの逸脱**: Python prototype の `Diagnostic.span: Optional[SourceSpan]` と異なり、v0 の `span` は non-optional(diagnostics の発生源が tree-sitter の recovery node に限られるため、常に実 span を持つ)
  - `SourceSpan` の `start_point`/`end_point`(line/column)は v0 では追加しなかった(`replace` 内部の `point_at` helper はあるが非公開のまま)。公開 API としての point 情報は「次の判断が必要なもの」として `Decisions Needed` に積む
  - Python: `_astars.parse_bytes(source: bytes, lang)` / `_astars.parse_file(path: str, lang)`(I/O 失敗は `OSError`)/ `PySyntaxTree.diagnostics() -> list[PyDiagnostic]`(`severity` は `"error"` という plain string)を追加。Node: `parseBytes(source: Buffer, lang)` / `parseFile(path: string, lang)`(I/O 失敗は throw)/ `JsSyntaxTree.diagnostics() -> JsDiagnostic[]` を追加。両言語で `cargo test` / `clippy -- -D warnings` が通り、`maturin develop` / `npm run build:debug` 後に実際に non-UTF-8 bytes の parse・存在しないファイルの parse_file・構文エラーのある source の diagnostics を確認済み
- `main` の最新 release は `v0.1.0`
- `Decisions Needed` に残っていた4項目を決定した。(1) `astars-core` の複数 crate 分割は見送り、単一 crate のまま(現状困っていない)。(2) `pyproject.toml`/`package.json` 追加タイミングは実装済みのため項目として解消。(3) `SourceSpan` の `start_point`/`end_point`(line/column)公開は Not Now に回す(具体的な消費者が出てから) → **2026-10-23、方針転換して実装した(詳細下記)**。(4) `parse_file` の非 UTF-8 encoding サポートは実装した — `encoding_rs` を追加し、`parse_file(path, lang, encoding)` が WHATWG Encoding Standard のラベル(`"utf-8"`、`"shift_jis"` 等)で decode してから parse する形にした。decode は `encoding_rs::Encoding::decode` が常に valid UTF-8 の `String` を返すため、不明なラベルは `AstarsError::UnsupportedEncoding` で弾く。Python は `encoding="utf-8"` のデフォルト引数(不正ラベルは `ValueError`)、Node は `encoding?: string` の optional 引数(デフォルト `"utf-8"`)で公開し、両言語で実際に Shift-JIS ファイルの decode・不明ラベルのエラーを確認済み
- `SourceSpan` の point(line/column)情報を実装した。`astars-core` に `Point { line, column }`(0-based、byte column)を新設し、`SyntaxTree::point_at(byte_offset) -> Point` で任意の byte offset を変換できるようにした。既存の `replace` 内部ヘルパー(`tree_sitter::Point` を返す private 関数)と行/列スキャンのロジックを共有している(`line_col_at`)。`ByteSpan` 自体には point を持たせず(`Copy` で頻繁に使われる型を重くしないため)、`point_at` を span の start/end byte に対して個別に呼ぶ形にした。Python は `point_at(byte_offset) -> (int, int)`、Node は `pointAt(byteOffset) -> [number, number]` として公開し、両言語で実際に動作確認済み
- `examples/python/basic_parse.py` / `examples/node/basic-parse.js` を v0 scope 全体に合わせて更新した。従来は read-only query API(`parse_str`/`walk`/`find`/`span_of`/`source_of`/`node_info`/`node_at`/`dump`)しかデモしていなかったが、`point_at`・編集 primitive(`replace`/`unchanged_in`)・`parse_bytes`・`parse_file`・`diagnostics` を追加し、Python/Node 両方で実際に実行して出力を確認した

## Next Action

v0 scope(旧 Python `0.1.0` 相当の query API + 編集 primitive v1 + `parse_file` encoding 対応 + point API)は一通り実装・公開が完了した。次に着手する作業は未着手。

完了条件:

- [x] Python と Node 両方の binding spike が動作する(parse できて、何らかの値が両言語から取得できる)
- [x] Rust core v0 scope が文書化されている
- [x] `walk` / `find` / `node_at` / `span_of` / `source_of` が `astars-core` に実装されている
- [x] `SyntaxTree` が Python / Node 両方の binding から実際に使える(`node_info` / `dump` を含む)
- [x] `replace` + `unchanged_in` が `astars-core` で動作する(編集して、意図した箇所以外が変わっていないことを確認できる)
- [x] `replace` + `unchanged_in` が Python / Node binding からも使える
- [x] `point_at` が `astars-core` に実装され、Python / Node binding からも使える
- [x] `parse_bytes` / `parse_file` / `diagnostics` が `astars-core` に実装され、Python / Node binding からも使える

## Decided: Release 0.1.1 は出さない

`0.1.1` は release tooling と documentation の maintenance release として計画していたが、Rust 移行に集中するため出さないことを決定した。`v0.1.0` を Python line の最終 release とする。

## Paused: Python Source Mapping Stabilization (Rust 移行待ち)

以下は `feature/0.2-source-mapping` 上で進めていたが、Rust 移行方針により一時停止する。設計判断そのもの(tie-breaker、boundary 挙動、mapping failure の扱いなど)は Rust core 設計時に再利用する前提で、[SOURCE_MAPPING_PLAN.ja.md](SOURCE_MAPPING_PLAN.ja.md) にそのまま残す。

- `SyntaxGraph.ast_at()` / `SourceUnit.node_at()` の選択規則 test 固定
- mapping failure の扱いの test 化
- Documentation and cleanup 項目
- `0.1.1` release 後の `develop` 取り込みと `0.2.0` 統合

## Decisions Needed

現時点で未決定の項目はない(2026-10-23 に4項目すべて決定。詳細は `Current Snapshot` 参照)。

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

次の項目は重要だが、具体的な消費者が出てくるまで着手しない。

- 編集 primitive の本格実装(v1 の `replace`/`unchanged_in` を超える範囲: insert/delete 専用メソッド、Piece Table 化、系譜追跡、名前/kind アドレス指定。詳細は `EDIT_MODEL.ja.md` の「v1 のスコープ外」)
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

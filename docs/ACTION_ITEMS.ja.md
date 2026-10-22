# Astars Action Items

最終確認日: 2026-10-23

この文書は、作業を再開するときに最初に読むための短期 action item 一覧である。
背景や設計理由は各計画文書に残し、ここでは「次に何をするか」と完了条件だけを管理する。実装の詳細な経緯は `git log` を参照。

関連文書:

- [STRATEGY.ja.md](STRATEGY.ja.md) — ビジョンと Core Differentiator(「強みの実現状況」が何を実現しようとしているかの根拠)
- [architecture/ARCHITECTURE.ja.md](architecture/ARCHITECTURE.ja.md) — クラス図と v0 scope
- [architecture/EDIT_MODEL.ja.md](architecture/EDIT_MODEL.ja.md) — 編集まわりの設計根拠、シナリオ、操作リスト
- [NEXT_RELEASE_PLAN.ja.md](NEXT_RELEASE_PLAN.ja.md)
- [SOURCE_MAPPING_PLAN.ja.md](SOURCE_MAPPING_PLAN.ja.md)
- [RELEASE_STRATEGY.ja.md](RELEASE_STRATEGY.ja.md)
- [ROADMAP.ja.md](ROADMAP.ja.md)

## v0 Scope: 完了

Rust core(`crates/astars-core`)+ Python/Node binding(`bindings/python`、`bindings/node`)で、以下を実装・動作確認済み(Python/Node 両方で実機確認)。設計の詳細は [architecture/ARCHITECTURE.ja.md](architecture/ARCHITECTURE.ja.md) のクラス図、編集まわりの根拠は [architecture/EDIT_MODEL.ja.md](architecture/EDIT_MODEL.ja.md) を参照。

- monorepo 構成(`crates/astars-core` + `bindings/python` + `bindings/node`)。クラス図は draw.io から Mermaid に移行済み
- parse: `parse_str` / `parse_bytes` / `parse_file`(`parse_file` は WHATWG encoding ラベル対応、`encoding_rs` 使用)
- query: `walk` / `find(kind)` / `node_at(offset)` / `span_of` / `source_of` / `point_at(byte_offset)`(0-based line/column)
- 編集 primitive(v1): `replace(target, new_text)` + `unchanged_in(id, edit)`(`tree.edit()` + `changed_ranges` ベース、`EDIT_MODEL.ja.md` 参照)
- diagnostics: parser recovery(`ERROR`/`MISSING` node)の公開
- examples(`examples/python/basic_parse.py` / `examples/node/basic-parse.js`)を上記全機能のデモに更新済み
- `main` の最新 release は `v0.1.0`(Python-only 時代の最終 release。Rust core は PyPI/npm に未公開、build from source のみ)

2026-10-21、AWS が Kiro IDE 向けに AST ベースの構造化編集を公開したことを受け、v0 scope の残作業より編集 primitive(`EDIT_MODEL.ja.md` 操作7・8)の実装を優先する方針に転換した(経緯は git log 参照)。Kiro は特定 IDE に閉じた内製機能であり、複数ランタイムでの再利用性と「編集を結果解析 loop の一部として扱う」点は Astars 固有の強みとして残る、という判断による。

完了条件:

- [x] Python と Node 両方の binding が動作する(parse できて、何らかの値が両言語から取得できる)
- [x] Rust core v0 scope が文書化されている
- [x] `walk` / `find` / `node_at` / `span_of` / `source_of` / `point_at` が `astars-core` に実装され、Python / Node binding からも使える
- [x] `SyntaxTree` が Python / Node 両方の binding から実際に使える(`node_info` / `dump` を含む)
- [x] `replace` + `unchanged_in` が `astars-core` で動作し、Python / Node binding からも使える
- [x] `parse_bytes` / `parse_file`(encoding 対応)/ `diagnostics` が `astars-core` に実装され、Python / Node binding からも使える

## 強みの実現状況

`STRATEGY.ja.md` の「Core Differentiator」が主張する強みに対して、v0 完了時点でどこまで実装・証明できているかを 4 つに分けて追跡する(2026-10-23 新設。旧 `Not Now` を強み軸で再整理した)。

### 1. Source-faithful かつ編集可能な構造(parse → query → edit → re-analyze の loop)

`EDIT_MODEL.ja.md` の操作リストに対応。

- [x] 操作1-6(parent/children、walk、find、node_at、span_of、source_of)
- [x] 操作7(編集 primitive: `replace`)
- [x] 操作8(編集前後の node 同一性比較: `unchanged_in`)
- [x] 操作11(部分木の一括 export: `dump`)
- [x] 操作12(node を値として FFI 境界を越えられる制約)
- [ ] 操作9(派生系譜の追跡 — variant が元のどの node から来たかを追跡する台帳。シナリオB で必須)
- [ ] 操作10(名前/kind ベースのアドレス指定 — 「名前 `hello` の関数」を一発で引く。シナリオA の核心)
- [ ] 操作13(独立な2木の構造的 diff。2026-10-23 新規追加、計画中。v1 は textual diff + 既存の `tree.edit()` 機構で代替し、v2 で GumTree による node matching に置き換える方針。詳細は `EDIT_MODEL.ja.md` の「構造的 diff(操作13)の設計」参照)

土台(1-8, 11-12)はできているが、この強みを強みたらしめる 9・10・13 が手つかずのまま。

### 2. 複数ランタイムでの再利用性

- [x] Python/Node 両 binding が v0 API 全体で完全にパリティ(実機で動作確認済み)
- [ ] PyPI / npm への公開(現状 build from source のみ)

### 3. LLM エージェント向け名前/kind ベース構造化編集

- [x] `replace` + `unchanged_in` による「編集して暴走していないか確認する」ワークフローの土台
- [ ] 操作10(名前/kind アドレス指定)— 強み1と同じ項目。これが無いと「diff より優れている」という主張の核心部分が未実証(現状は `find(kind)` で候補を絞ってから利用者側で名前を確認する形)
- [ ] selector DSL

### 4. ecosystem 中核としての軽量 engine

- [ ] downstream package の実装例が1つもない(`astars-metrics` 等は `STRATEGY.ja.md` 上の構想のみ)
- [ ] シナリオB(変異生成パイプライン)・C(embedding/LLM評価)・D(可視化)・E(構造的 diff、`astars-code-review` の土台)をエンドツーエンドで動かす実例がない

### その他(強みと直接紐づかないが明示的に見送っているもの)

- stable CST / `RawSyntaxNode` public API
- semantic analysis
- multi-language support(Python 以外の対象言語)
- legacy API compatibility(`AParser`/`APruner`/`ATraverser` 等)

いずれも「具体的な消費者が出てくるまで着手しない」方針のままである。

## Decided: Release 0.1.1 は出さない

`0.1.1` は release tooling と documentation の maintenance release として計画していたが、Rust 移行に集中するため出さないことを決定した。`v0.1.0` を Python line の最終 release とする。

## Completed on the Python Prototype (`feature/0.2-source-mapping`)

Rust 移行後も設計の参照点として記録を残す。tie-breaker・1-based helper・`SourceText` の扱いなど、ここで固めた方針は v0 の Rust 実装(`node_at` の再帰探索による具体性優先、`Point` の 0-based 設計、`SyntaxTree` 内に閉じた source 保持)で一貫して踏襲済み。不連続な raw spans の covering span 化のみ、v0 が rule 正規化(`SyntaxGraph` 相当)を持たないため該当なし — 導入時に再検討する。

- [x] source mapping の public behavior を文書化した
- [x] invalid offset を `AstarsError` とする方針を固定した
- [x] foreign `SourceUnit` の node を `AstarsError` とする方針を固定した
- [x] EOF offset で `node_at()` が `None` を返すようにした
- [x] Unicode source の UTF-8 byte offset test を追加した
- [x] non-UTF-8 file input の mapping test を追加した
- [x] zero-width diagnostic span の test を追加した
- [x] `SourceText` internal model を導入した
- [x] `SourceUnit` の validation / slicing / point conversion を `SourceText` に寄せた

## Update Rule

- 作業を開始した item は、その commit または pull request で checkbox を更新する
- 新しい短期作業はまずこの文書に追加し、詳細設計が必要なら専用 plan に分ける
- release、branch、実装言語の方針が変わったら `v0 Scope: 完了` も更新する
- 「強みの実現状況」の項目に手をつけたら、該当する checkbox を更新する

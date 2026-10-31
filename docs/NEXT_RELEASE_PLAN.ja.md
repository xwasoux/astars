# Astars 次期リリース計画

関連文書:

- [ACTION_ITEMS.ja.md](ACTION_ITEMS.ja.md)
- [RELEASE_STRATEGY.ja.md](RELEASE_STRATEGY.ja.md)
- [architecture/EDIT_MODEL.ja.md](architecture/EDIT_MODEL.ja.md)

この文書は、Rust core(`crates/astars-core` + `bindings/python` + `bindings/node`)の version ごとの release scope を管理する。`v0.1.0` は旧 Python-only 実装の最終 release であり、ここで扱う `v0.2.0` 以降は Rust core の release である。

## Current Baseline

v0 scope(parse/query/edit primitive v1/diagnostics)は Rust core + Python/Node binding として実装・動作確認済みで、`main` に `v0.2.0` として tag 済みである。詳細は [ACTION_ITEMS.ja.md](ACTION_ITEMS.ja.md) の「v0 Scope: 完了」を参照。

## v0.2.0: 最初の Rust Release(完了)

`v0.2.0` の目的は、エンジンの中身を増やすことではなく、すでに完成している v0 scope を実際に PyPI / npm へ公開することだった。完了している。

スコープと進捗:

- [x] `astars-core` / `astars-py` / `astars-node` の version を `0.2.0` に揃える
- [x] Python wheel を `maturin build --release` で作り、クリーンな venv への install smoke test を通した
- [x] Node package を `napi build --platform --release` で作り、example で動作確認した
- [x] `main` に merge し、`v0.2.0` tag を打って push した
- [x] Python wheel を PyPI へ `maturin publish` する(`astars-py` 0.2.0 を publish 済み。project-scoped token は新規 project には使えないため、初回は account-scoped token で publish した)
- [x] Node package を npm へ `@astars/native` として `npm publish --access public` する(`@astars` organization が未作成だったため、npmjs.com で作成してから publish した)
- 新機能は追加しない

やらないこと:

- 操作9(系譜追跡)、操作10(名前/kind アドレス指定)の実装
- 操作13(構造的 diff)の実装
- downstream package の実装

## v0.3.0 以降の候補

優先順位は固定しない。`ACTION_ITEMS.ja.md` の「強みの実現状況」が未解決のまま残している項目から選ぶ。

- **操作9・10**: 系譜追跡 + 名前/kind ベースのアドレス指定。強み1・3(source-faithful な編集 loop、LLM エージェント向け構造化編集)の核心
- **操作13 v1**: textual diff + `tree.edit()` ベースの構造的 diff(`astars-code-review` の土台)。設計は `EDIT_MODEL.ja.md` の「構造的 diff(操作13)の設計」
- **downstream package 1本の実証**: `astars-metrics` など軽量なものを1つ作り、強み4(ecosystem 中核)を初めて実証する
- **操作13 v2**: GumTree ベースの node matching(構造的 diff の最終形態)
- 他言語対応、semantic analysis などは `ACTION_ITEMS.ja.md` の「その他」に残る長期項目

## Decision Gates

### `v0.2.0` に進む条件

- v0 scope の build/test/clippy が workspace 全体で通る
- Python/Node 両 binding の examples が実際に動く
- legacy な docs/code が残っていない(確認済み)

### `v0.3.0` 以降に進む条件

- 次に着手する項目(操作9・10・13、downstream package のいずれか)を1つに絞る
- 複数 version にまたがる大きな変更を1 release に詰め込まない

# Astars Source Mapping 計画

ステータス: Python prototype(`prototype-python/`、frozen reference)で検証済み

関連文書:

- [STRATEGY.ja.md](STRATEGY.ja.md)
- [architecture/ARCHITECTURE.ja.md](architecture/ARCHITECTURE.ja.md)
- [ACTION_ITEMS.ja.md](ACTION_ITEMS.ja.md)

この文書はもともと、旧 Python 実装(`astars.SourceUnit` ベースの API)向けに source mapping の public behavior / internal responsibility を定義する計画書だった。その API 自体は Rust core への移行で置き換わっているが、ここで固めた設計判断は Rust 実装(`crates/astars-core`)にそのまま引き継がれているため、この節だけ残す。

## Resolved Decisions

- invalid offset は `AstarsError` とする
- 別 `SourceUnit` 由来 node は `AstarsError` とする
- EOF offset は `node_at` で `None` を返す
- zero-width span は `node_at` の対象に含めない

Rust 実装での対応: `SyntaxTree::node_at` は EOF offset で `None` を返す(`ACTION_ITEMS.ja.md` の「Completed on the Python Prototype」参照)。`NodeId` の無効値や他 tree 由来の `NodeId` を渡した場合は `AstarsError` ではなく panic にする設計に変更した(バインディング層で例外に変換する方針。詳細は `architecture/ARCHITECTURE.ja.md` の `NodeId::from_u32` のドキュメントコメント参照)。

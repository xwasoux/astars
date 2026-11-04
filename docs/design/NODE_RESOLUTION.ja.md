# Node Resolution: 無効値の扱い

関連文書:

- [../strategy/STRATEGY.ja.md](../strategy/STRATEGY.ja.md)
- [ARCHITECTURE.ja.md](ARCHITECTURE.ja.md)

`SyntaxTree::node_at` / `NodeId` に無効な値を渡した場合の設計判断。

- EOF offset は `node_at` で `None` を返す
- zero-width span は `node_at` の対象に含めない
- 無効な `NodeId`、または他の tree 由来の `NodeId` を渡した場合は `AstarsError` を返さず panic する(バインディング層で例外に変換する方針。詳細は `NodeId::from_u32` のドキュメントコメント参照)

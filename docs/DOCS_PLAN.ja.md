# Astars ドキュメント計画

ステータス: 継続更新中

関連戦略: [STRATEGY.ja.md](STRATEGY.ja.md)

この文書は、Astars のドキュメントをどの粒度に分けるかを整理するための叩き台である。

当面は日本語版を primary document とする。英語版は、戦略文書群が安定してからまとめて同期する。

想定する文書構成は次の通り。

- `STRATEGY.ja.md`: 上位方針、独自性、ecosystem、trade-off
- `API_STRATEGY.ja.md`: public API、extension API、internal API の境界
- `CONCEPTS.ja.md`: `RawSyntaxNode`, CST, AST, `SyntaxGraph`, source span の概念定義
- `USE_CASES.ja.md`: research / practical use cases の詳細
- `ARCHITECTURE.ja.md`: module 構成、依存方向、data flow
- `SOURCE_MAPPING_PLAN.ja.md`: source mapping の public behavior と internal responsibility
- `ROADMAP.ja.md`: 実装 phase、milestone、release plan
- `MIGRATION.ja.md`: 旧 API から新 API への移行方針
- `V0_PLAN.ja.md`: v0 public API 実装の具体的な作業計画
- `NEXT_RELEASE_PLAN.ja.md`: `0.1.1` と `0.2.0` の作業分離
- `RELEASE_STRATEGY.ja.md`: branch strategy、versioning、PyPI/TestPyPI publish 方針

分割の基準は、読む人の関心である。戦略判断を知りたい人は `STRATEGY`、実装に入る人は `ARCHITECTURE`、downstream package を作る人は `API_STRATEGY` と `CONCEPTS` を読む、という状態を目指す。

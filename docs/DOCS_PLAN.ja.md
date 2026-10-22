# Astars ドキュメント計画

ステータス: 継続更新中

関連戦略: [STRATEGY.ja.md](STRATEGY.ja.md)

この文書は、Astars のドキュメントをどの粒度に分けるかを整理するための叩き台である。

当面は日本語版を primary document とする。英語版は、戦略文書群が安定してからまとめて同期する。

想定する文書構成は次の通り。

- `ACTION_ITEMS.ja.md`: 現在地、直近の作業順、完了条件、強みの実現状況
- `STRATEGY.ja.md`: 上位方針、独自性、ecosystem、trade-off
- `USE_CASES.ja.md`: research / practical use cases の詳細
- `architecture/ARCHITECTURE.ja.md`: module 構成、依存方向、クラス図(Mermaid)
- `architecture/EDIT_MODEL.ja.md`: 編集・diff まわりのシナリオ、操作リスト、設計根拠
- `SOURCE_MAPPING_PLAN.ja.md`: Python prototype で検証した source mapping の設計判断(Rust 設計の参照点)
- `ROADMAP.ja.md`: 導入ストーリー
- `NEXT_RELEASE_PLAN.ja.md`: version ごとの release scope
- `RELEASE_STRATEGY.ja.md`: branch strategy、versioning、publish 方針

分割の基準は、読む人の関心である。戦略判断を知りたい人は `STRATEGY`、実装に入る人は `ARCHITECTURE` / `EDIT_MODEL`、次に何をやるかを知りたい人は `ACTION_ITEMS` / `NEXT_RELEASE_PLAN` を読む、という状態を目指す。

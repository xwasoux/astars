# Astars Docs

関連戦略: [strategy/STRATEGY.ja.md](strategy/STRATEGY.ja.md)

この文書は、`docs/` 以下のドキュメントがどの粒度・どのディレクトリに分かれているかを示す索引である。

当面は日本語版を primary document とする。英語版は、戦略文書群が安定してからまとめて同期する。

文書構成は次の通り。分割の基準は、読む人の関心である。

- `docs/` 直下: どのカテゴリにも固定しない、または常に最初に読む文書
  - `README.md`: 本書。ドキュメント構成の索引
  - `ACTION_ITEMS.ja.md`: 現在地、直近の作業順、完了条件、強みの実現状況
- `strategy/`: なぜ作るか、何を目指すか
  - `STRATEGY.ja.md`: 上位方針、独自性、ecosystem、trade-off
  - `USE_CASES.ja.md`: research / practical use cases の詳細
  - `ROADMAP.ja.md`: 導入ストーリー
- `design/`: どう作るか
  - `ARCHITECTURE.ja.md`: module 構成、依存方向、クラス図(Mermaid)
  - `EDIT_MODEL.ja.md`: 編集・diff まわりのシナリオ、操作リスト、設計根拠
  - `NODE_RESOLUTION.ja.md`: `node_at`/`NodeId` の無効値の扱いに関する設計判断
  - `SOURCE_MODEL.ja.md`: 文字列の lossy decode、`Point.column` の座標系、diagnostics の取得元に関する設計判断
  - `img/`、`repo-structure.drawio.svg`: 上記の文書で参照する図
- `release/`: いつ・どの順で出すか
  - `NEXT_RELEASE_PLAN.ja.md`: version ごとの release scope
  - `RELEASE_STRATEGY.ja.md`: branch strategy、versioning、publish 方針

戦略判断を知りたい人は `strategy/`、実装に入る人は `design/`、次に何をやるかを知りたい人は `ACTION_ITEMS.ja.md` / `release/NEXT_RELEASE_PLAN.ja.md` を読む、という状態を目指す。

# Astars Docs

関連戦略: [strategy/STRATEGY.ja.md](strategy/STRATEGY.ja.md)

この文書は、`docs/` 以下のドキュメントがどの粒度・どのディレクトリに分かれているかを示す索引である。

当面は日本語版を primary document とする。英語版は、戦略文書群が安定してからまとめて同期する。

文書構成は次の通り。分割の基準は、読む人の関心である。

- `docs/` 直下: どのカテゴリにも固定しない、または常に最初に読む文書
  - `README.md`: 本書。ドキュメント構成の索引
  - `ACTION_ITEMS.ja.md`: 現在地、直近の作業順、完了条件、capability status
- `strategy/`: なぜ作るか、何を目指すか
  - `STRATEGY.ja.md`: 上位方針、独自性、ecosystem、trade-off
  - `USE_CASES.ja.md`: research / practical use cases の詳細
  - `ROADMAP.ja.md`: 導入ストーリー
- `design/`: どう作るか
  - `README.md`: design 文書の分割方針、読む順序、記載先の索引
  - `PROGRAM_MODEL.ja.md`: Program State、structure layer、node identity、incomplete state
  - `SOURCE_MODEL.ja.md`: source representation、座標、structureとのmapping、projection
  - `OPERATION_MODEL.ja.md`: structural operationの意味論、適用、replay、composition
  - `PROVENANCE_MODEL.ja.md`: state / operation / nodeのlineage
  - `ARCHITECTURE.ja.md`: 各modelのlayer / crate / bindingへの配置とcurrent / target gap
  - `decisions/`: 個別の設計判断と理由を残すADR
- `release/`: いつ・どの順で出すか
  - `RELEASE_POLICY.ja.md`: release unit、versioning、compatibility、tagの規約
  - `RELEASE_PROCESS.ja.md`: build、検証、tag、publishの反復手順
  - `NEXT_RELEASE.ja.md`: 次の1releaseのscope、non-goal、evidence gate

戦略判断を知りたい人は`strategy/`、実装に入る人は`design/`、次に何をやるかを知りたい人は`ACTION_ITEMS.ja.md` / `release/NEXT_RELEASE.ja.md`を読む、という状態を目指す。

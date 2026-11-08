# Astars Architecture Decision Records

このディレクトリは、Astars の設計上の選択と、その理由・代替案・影響を記録する。

ADR は target model の代わりではない。現在有効な意味論と不変条件は `docs/design/*_MODEL.ja.md` に記載し、ADR には「なぜその選択を採用したか」を残す。

## File Naming

```text
NNNN-short-decision-title.ja.md
```

- `NNNN` は4桁の連番
- 一度割り当てた番号は再利用しない
- superseded になった ADR も削除しない

## Template

```markdown
# Decision title

Status: Proposed | Accepted | Superseded

## Context

この判断が必要になった背景と制約。

## Decision

採用する選択。

## Consequences

得られる性質、受け入れる制約、migrationへの影響。

## Alternatives

検討した代替案と採用しなかった理由。

## Related Documents

関連するmodel、implementation、test、置き換え先ADR。
```

## Decision Index

- [0001: State-local Node Identity and Controlled Errors](0001-state-local-node-identity-and-controlled-errors.ja.md)
- [0002: Stage 2 Source Splice and Incremental Re-parse](0002-stage-2-source-splice-and-incremental-reparse.ja.md)
- [0003: Analysis-neutral Field Navigation](0003-analysis-neutral-field-navigation.ja.md)
- [0004: Independent Source Diff Is Inferred Correspondence](0004-independent-source-diff-is-inferred.ja.md)

今後のADR候補:

- `Point.column`にbyte columnを採用する理由
- `source_of`をlossy UTF-8 viewとする理由
- parser recovery diagnosticsをtree-sitterの`ERROR` / `MISSING`から得る理由

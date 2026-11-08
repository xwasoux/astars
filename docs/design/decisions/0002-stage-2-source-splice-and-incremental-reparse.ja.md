# Stage 2 Source Splice and Incremental Re-parse

Status: Accepted

## Context

Stage 2では、nodeをtargetにしてsourceを編集し、編集後もquery可能なsyntax structureを返す必要がある。tree-sitterは`InputEdit`とincremental parseを提供するが、source text自体は編集しない。

将来のgraph-native operationを待たずに検証可能な最小経路を作る一方、incremental parser reuseをnode identityやprovenanceと誤認しない設計が必要である。

## Decision

Stage 2のstructure-addressed editは、次の経路を使う。

1. target nodeのspanをinput state上で解決する
2. working source bytesへspliceを適用し、新しいsource revisionを作る
3. old parser treeへ`InputEdit`を通知する
4. edited old treeを渡してincremental re-parseする
5. 新しい`SyntaxTree`とold / newそれぞれのchanged rangeを返す

最小primitiveは現行の`replace(target, new_text)`とする。insert / deleteはoperation semanticsとして区別し得るが、Stage 2のsource適用機構はreplacementへloweringできる。

input stateは破壊せず、結果は新しいstate snapshotとして扱う。source storageは当面連続`Vec<u8>`とし、Piece Table等は計測で必要性が示された時点で導入する。

## Consequences

- old / new changed rangeは異なるSource Revisionの座標なので分けて保持する
- parser incremental reuseは性能上の実装詳細であり、cross-state NodeId correspondenceを保証しない
- invalidな編集結果も、parser recovery diagnosticsを持つ新しいstateとして返し得る
- source splice、parser notification、re-parseを一つのoperation application pipelineとして検証する
- repeated editingのcopy costは当面受け入れ、benchmarkなしにPiece Tableを導入しない

## Alternatives

### 毎回from-scratch parseする

意味上は可能だが、Stage 2で利用できるincremental parseとchanged rangeを捨てるため、標準経路にはしない。結果の意味論はincremental parseへ依存させない。

### Treeだけを直接変更する

sourceとの対応を失い、Stage 2のsource-faithful editingを満たさないため採用しない。graph-native editはStage 5で別途扱う。

### 最初からPiece Tableを導入する

性能問題が未計測で、Source Modelとoperation semanticsの検証を遅らせるため採用しない。

## Related Documents

- [../SOURCE_MODEL.ja.md](../SOURCE_MODEL.ja.md)
- [../OPERATION_MODEL.ja.md](../OPERATION_MODEL.ja.md)
- [../ARCHITECTURE.ja.md](../ARCHITECTURE.ja.md)
- [../../strategy/ROADMAP.ja.md](../../strategy/ROADMAP.ja.md)

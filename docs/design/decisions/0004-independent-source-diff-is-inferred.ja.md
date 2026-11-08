# Independent Source Diff Is Inferred Correspondence

Status: Accepted

## Context

`replace`のような既知operationで繋がったstateと、gitの前後revisionのように独立して与えられた二sourceでは、利用できる根拠が異なる。現行`diff_with`はline-based Myers diffを`InputEdit`列へ変換し、tree-sitterのchanged rangeを得ることでadded / removed / unchanged相当を近似している。

この方法はrename、move、modify、split、mergeのnode correspondenceを推定しない。既知operationのlineageとして扱うと、将来のProvenance Modelで誤った確実性を与える。

## Decision

- 独立した二stateの比較は、既知operationによるlineageではなくinferred diffとして扱う
- 現行`diff_with`はStage 2のtextual approximationであり、Provenance Graphの根拠にはしない
- line diffの各hunkをbyte rangeへ変換し、後方から`InputEdit`を適用して一度re-parseする現行方式を維持する
- old / new nodeの分類はchanged rangeとのspan overlapに限定する
- `NodeId`同士の対応、rename / move / modify等を返さない
- 将来のstructural matchingはevidence、algorithm、confidenceを持つinferred correspondenceとして追加する

## Consequences

- `diff_with`とknown operationが同じ`EditResult`を返す現行APIには意味上の曖昧さが残る
- `unchanged`はidentityではなく「changed rangeと重ならない」という限定的なqueryである
- GumTree等を導入しても、推定結果をknown lineageへ昇格させない
- diff algorithmを差し替えてもProgram State / Operationのidentity contractは変えない

## Alternatives

### `diff_with`を既知operation列として記録する

text hunkは一つの変換手順にはなるが、実際の編集履歴やnode由来を証明しないため採用しない。

### Added / Removed / Unchanged enumをcoreへ固定する

現行近似だけを最終的なstructural relationに見せてしまうため採用しない。relation vocabularyはProvenance Model側で発展させる。

### 直ちにGumTree相当を実装する

Stage 2の検証範囲を超える。まずknown lineageとinferred correspondenceの境界を固定する。

## Related Documents

- [../OPERATION_MODEL.ja.md](../OPERATION_MODEL.ja.md)
- [../PROVENANCE_MODEL.ja.md](../PROVENANCE_MODEL.ja.md)
- [../SOURCE_MODEL.ja.md](../SOURCE_MODEL.ja.md)
- [../../strategy/ROADMAP.ja.md](../../strategy/ROADMAP.ja.md)

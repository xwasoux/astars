# State-local Node Identity and Controlled Errors

Status: Accepted

## Context

現行`NodeId(u32)`は、一つの`SyntaxTree`内のarena indexである。同じ数値でも別treeでは別nodeを指し得るため、cross-state identityには使えない。

旧`NODE_RESOLUTION.ja.md`では、invalid / foreign `NodeId`をpanicさせ、bindingで例外化する方針としていた。しかしcoreで起きたpanicをbindingが常に安全に回収できるとは限らず、外部入力を受けるpublic APIの契約としても弱い。operation replayやLLM tool inputを扱う段階では、誤ったstateへのtarget適用を通常のvalidation failureとして表現する必要がある。

## Decision

- `NodeId`のidentity scopeは、一つのProgram State内の一つのstructureとする
- cross-state relationには`NodeId`の数値比較ではなくProvenance Modelのcorrespondenceを使う
- public APIはinvalid / foreign / stale / out-of-range `NodeId`をpanicではなく制御されたerrorとして返す
- bindingはcore errorを各runtimeのexception / error valueへ変換する
- `node_at`はhalf-open spanに従い、EOFでは`None`を返す
- zero-width nodeは通常のpoint lookup対象に含めず、必要な場合は専用のquery semanticsを定義する

現行実装のpanicはこのdecisionに対する既知のgapであり、互換性を確認しながら移行する。

## Consequences

- operation targetはinput stateへの所属を検証できなければならない
- cross-state stable IDを`NodeId`へ後付けしない
- query APIの「見つからない」と「入力が不正」を区別する必要がある
- core APIの一部は`Option`だけでなく`Result`を返す形へ変わり得る
- bindingごとに異なるvalidation semanticsを実装しない

## Alternatives

### Invalid IDをpanicさせる

内部invariant違反の検出には単純だが、public input、FFI、operation replayには適さないため採用しない。

### NodeIdをglobal stable IDにする

parseごとにnode集合が再構築され、move / split / mergeも発生し得る。local lookup identityとcross-state correspondenceを混同するため採用しない。

### すべてのlookupを`Option`にする

対象が存在しない場合と、foreign ID等の契約違反を区別できないため採用しない。

## Related Documents

- [../PROGRAM_MODEL.ja.md](../PROGRAM_MODEL.ja.md)
- [../SOURCE_MODEL.ja.md](../SOURCE_MODEL.ja.md)
- [../OPERATION_MODEL.ja.md](../OPERATION_MODEL.ja.md)
- [../PROVENANCE_MODEL.ja.md](../PROVENANCE_MODEL.ja.md)

# Analysis-neutral Field Navigation

Status: Accepted

## Context

coding agentは「`hello`という関数」のようなstructure-based targetを必要とする。一方、`name`の意味はlanguage grammarやnode kindに依存する。coreへ`find_function_by_name`等を追加すると、特定analysisの意味論が増え続ける。

tree-sitter grammarは、childに`name`、`body`、`left`、`right`等のfield nameを付与している。これを汎用primitiveとして公開すれば、consumerがkind query、field navigation、source queryを組み合わせられる。

## Decision

- coreは`child_by_field_name(id, field_name)`のようなgrammar field navigationを提供する
- `name`を他のfieldから特別扱いしない
- `find_by_name`、`find_function_by_name`等のanalysis-specific convenience APIをcoreへ追加しない
- 複合selectorはconsumerまたは将来のquery layerがprimitiveを組み合わせて構築する
- FFI round tripを避ける価値がある汎用primitiveはPython / Node bindingへ直接公開する

## Consequences

- coreはlanguage grammarのfield vocabularyを運ぶが、そのdomain semanticsは解釈しない
- agent向けselector DSLを追加する場合も、core query primitiveと別layerにできる
- 単一child APIで不足するgrammarについては、要求が出た時点でmulti-value semanticsを設計する
- bindingは同じcore query semanticsを共有する

## Alternatives

### 名前検索専用API

短期的には便利だが、language / node kindごとの特例をcoreへ持ち込むため採用しない。

### DTOのsubtree dumpだけを使う

表現可能だが、単純なnavigationにも大きなexportとconsumer側走査が必要になるため、汎用field navigationを直接提供する。

### tree-sitter queryをそのままpublic APIにする

parser固有APIがpublic boundaryへ漏れ、将来のnormalized structureにも適用できないため採用しない。

## Related Documents

- [../PROGRAM_MODEL.ja.md](../PROGRAM_MODEL.ja.md)
- [../ARCHITECTURE.ja.md](../ARCHITECTURE.ja.md)
- [../../strategy/USE_CASES.ja.md](../../strategy/USE_CASES.ja.md)

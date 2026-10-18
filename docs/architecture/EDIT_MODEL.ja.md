# Astars Edit Model(Rust core)

ステータス: draft(データ構造設計の前段階)

関連文書:

- [ARCHITECTURE.ja.md](ARCHITECTURE.ja.md)
- [../STRATEGY.ja.md](../STRATEGY.ja.md)
- [../CONCEPTS.ja.md](../CONCEPTS.ja.md)(旧 Python 実装前提。`Edit Primitive` セクションの具体化が本書)
- [../ACTION_ITEMS.ja.md](../ACTION_ITEMS.ja.md)

この文書は、v0 scope の残作業(AST node 構造、`SyntaxGraph` 相当、query API)に着手する前に、「木構造のノード操作と、それに追従するテキスト編集をどう実現するか」を整理したものである。データ構造そのものの設計は、本書の結論を前提に別途進める。

## 背景: なぜこの整理が要るか

`STRATEGY.ja.md` のビジョンにある通り、Astars の核は「AST を自在に操れること」であり、「切り貼りした結果どうなるかを解析できること」が分析の一部である。つまり **編集(edit)は後付け機能ではなく、最初から想定すべき中心機能** である。

AST node 構造(kind、span、parent/children をどう持つか)を決める前に、「その node に対して何をしたいのか」を先に固定しないと、後から編集を前提にした作り直しが発生しやすい。本書はその「何をしたいか」を 4 つのシナリオと操作リストに落とし、次に「編集時にテキストと木がどう追従するか」を tree-sitter の機能と自前実装の分担として整理する。

## シナリオ

Astars の core が最終的に支える、具体的な利用シナリオ。`STRATEGY.ja.md` の想定利用者・downstream package 例と対応する。

### シナリオA: LLM coding agent による構造化編集

LLM が「関数 `hello` の本体を書き換えて」のように、diff や行番号ではなく名前/kind で編集対象を指定してくる(`STRATEGY.ja.md` の「LLM Coding Agent の編集形式」参照)。

1. 名前/kind で対象 node を特定する
2. 該当範囲を書き換えて新しい source を作る
3. 編集後、意図した箇所以外が変わっていないか確認したい(LLM の暴走検知)
4. Claude Code のような agent runtime(Node)と、研究用 harness(Python)の両方から呼べる必要がある

### シナリオB: 変異生成パイプライン(`astars-pruning`、リポジトリ群規模)

ある statement を削除したら何が起こるかを、リポジトリ全体で大量に試して評価したい。

1. 候補箇所を列挙する(kind filter + traverse)
2. 変異を適用して source variant を作る
3. 大量の variant の結果を、元のどの箇所に由来するか追跡して集計する(系譜の追跡)
4. Python から結果を集計する

### シナリオC: embedding / LLM 評価(`astars-llm-eval`)

構造をベクトル空間や LLM 入力として扱う(`STRATEGY.ja.md` の「グラフデータの問題として扱う」)。

1. node 間の関係をシリアライズして外に出す
2. Python から利用する

### シナリオD: 可視化(`astars-visualizer`)

パース結果をツリー図として描画したり、編集前後の差分をハイライトしたりする。

1. 木全体(または大きな部分木)を丸ごと辿って描画する
2. 編集前後で「このnodeは変わっていないか」をハイライトに使う

## 操作リスト

シナリオから導出した、Astars core が支えるべき操作。

### v0 で実装する

1. 親子ナビゲーション(parent / children)
2. traverse — 木全体を辿る(`walk`、kind filter あり)
3. `find(kind)`
4. `node_at(byte_offset)` — 位置 → node
5. `span_of(node)` — node → byte 範囲
6. `source_of(node)` — node → source のslice

### 将来実装するが、データ構造選択で詰ませたくない

7. **編集 primitive**: source の一部を書き換えて新しい tree/source を作る。8・9 が成立する前提
8. **編集前後の node 同一性比較**: このnodeは編集で変わっていないか(シナリオA・D)
9. **派生系譜の追跡**: この variant node は元のどの node から来たか(シナリオB)
10. **名前/kind ベースのアドレス指定**: byte offset とは別の軸で node を引く(シナリオA)
11. **部分木の一括 export**: node 一個ずつではなく、subtree をまとめて1回の FFI 呼び出しで取り出す(シナリオC・D。FFI 越しの逐次呼び出しは呼び出し回数分のオーバーヘッドが乗る)

### 制約(機能要求ではなく、全操作に効いてくる前提)

12. node は binding(Python/Node)に **値として** 渡せる必要がある。Rust の参照・lifetime を FFI 境界の外に持ち出せない

## 編集時のテキスト/木の追従: tree-sitter と自前実装の分担

操作 7〜9 を実現する上で、「編集でテキストが変わったとき、木がどう追従するか」が本体の論点になる。

### tree-sitter に任せられること

- **構文解析そのもの**(bytes → CST)
- **編集による offset の再計算**: `Tree::edit(InputEdit)` で古い木に変更範囲を伝えた上で、`parser.parse_with(callback, Some(&old_tree))` で再 parse すると、編集箇所より後ろにある node の byte offset を自動補正してくれる
- **変更されていない部分木の再利用**(incremental parsing。性能最適化を兼ねる)
- **2本の木の差分**: `Tree::changed_ranges(&old_tree, &new_tree)` で「どこが変わったか」を取得できる。ただし **同じ edit 系譜で繋がっている2本の木同士でしか使えない**(`tree.edit()` を経由せず独立に parse した2つの木には使えない)
- **source 読み出しの抽象化**: `parse_with` は callback 形式で source を読むため、連続した byte 配列である必要がない。次項の Piece Table と直結する

### 自前で実装する必要があること

- **テキスト編集の実行そのもの**: tree-sitter は「ここからここまでをこう変えた」という記述(`InputEdit`)を受け取るだけで、実際の文字列の置換・挿入・削除は行わない
- **効率的なテキスト格納**: 単純に `old[:start] + new + old[end:]` で文字列結合すると、編集のたびに全体コピー(O(n))が走る。シナリオB(リポジトリ規模で大量の変異を連続生成)ではこれが効いてくる。**Piece Table** のような、編集を O(編集量) で扱えるデータ構造で source text を持ち、`parse_with` の callback から直接読ませることで、連続 buffer への一本化を避ける
- **名前/kind アドレス指定**(操作10): tree-sitter の query 言語(`.scm`)で部分的に楽はできる可能性があるが、「関数名 `hello` で引く」のような意味的な検索は自前
- **edit 系譜を跨いだ系譜追跡**(操作9、シナリオB): `changed_ranges` は2本の関連木の間でしか効かないため、大量の variant が「どの original から来たか」の台帳は自前で持つ
- **独立に parse した木同士の比較**: 同じ edit 系譜でない2つの木(別ファイル、あるいは from-scratch 再 parse)を比較するなら、tree-sitter の仕組みは使えず自前の stable-id か構造比較が要る

## 決定した運用規約

**編集は常に `tree.edit()` + `parse_with(..., Some(&old_tree))` の経路で行い、そこから外れた独立 re-parse を避ける。**

注意: これは「木(②)だけを編集し、テキスト(①)は編集しない」という意味ではない。実際に変わるのは常にテキストである(Piece Table で保持・編集する)。決めているのは、**テキストの変更を木に反映する経路を1本に固定する** ことである。

- 経路A(避ける): テキストを書き換えた後、`parser.parse(new_text, None)` で独立に再 parse する。新しい木は古い木と無関係になり、`changed_ranges` が使えず、差分を自前で突き止める必要がある
- 経路B(採用): `old_tree.edit(InputEdit{...})` で古い木に変更範囲を伝えた上で、`parser.parse_with(callback, Some(&old_tree))` で再 parse する。新しい木は古い木の「続き」として生まれ、`changed_ranges` で差分が取れ、変わっていない部分木は tree-sitter 内部で再利用される

この規約により、操作8(編集前後の同一性比較)は、自前の stable-id machinery を最小限にしつつ、ほぼ tree-sitter の `changed_ranges` に乗せられる。操作9(系譜追跡)は `changed_ranges` の対象外(別系譜の variant 同士を跨ぐ)なので、引き続き自前の台帳が必要。

## Open Questions(データ構造設計で決めること)

- AST node を arena(index 参照)で持つか、他の方式にするか(操作12 の bindings 値渡し制約と、tree-sitter の `parse_with` callback をどう橋渡しするか)
- Piece Table の具体的な実装(自前 crate か、既存 crate を使うか)
- 操作9(系譜追跡)の台帳をどこに持つか(`astars-core` 内か、呼び出し側(downstream)に任せるか)
- 操作10(名前/kind アドレス指定)を tree-sitter query 言語の上に作るか、自前 traversal で作るか
- 操作11(部分木の一括 export)の具体的な API 形状(JSON 的な nested 構造を返すか、flat な配列 + 親子 index を返すか)

## Next Step

本書の結論を前提に、AST node のデータ構造(node が何を持つか、tree 全体をどう保持するか)の設計に進む。

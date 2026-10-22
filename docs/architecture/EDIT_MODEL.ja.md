# Astars Edit Model(Rust core)

ステータス: 編集 primitive(v1、操作7・8・11)は実装済み。操作9・10(系譜追跡、名前/kind アドレス指定)は Not Now(具体的な消費者待ち)。操作13(構造的 diff)は計画中 — v1(textual diff + 既存の `tree.edit()` 機構)を暫定実装し、v2(GumTree による node matching)を最終形態とする

関連文書:

- [ARCHITECTURE.ja.md](ARCHITECTURE.ja.md)
- [../STRATEGY.ja.md](../STRATEGY.ja.md)
- [../ACTION_ITEMS.ja.md](../ACTION_ITEMS.ja.md)

この文書は、v0 scope の AST node 構造(`SyntaxTree`/`SyntaxNode`)に着手する前に、「木構造のノード操作と、それに追従するテキスト編集をどう実現するか」を整理したものである。データ構造そのものは [ARCHITECTURE.ja.md](ARCHITECTURE.ja.md) の「astars-core」クラス図の設計で実装済み。本書の後半(「編集 primitive(v1)の設計」節)は、そのデータ構造を前提に、操作7・8(編集 primitive と編集前後比較)を実装するための設計を追記したものである。

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

### シナリオE: 構造的 diff(`astars-code-review`)

git の前後コミットのような、`tree.edit()` 系譜で繋がっていない独立な2つの source(同じファイルの2バージョン)を比較し、node 単位で何が変わったかを知りたい。操作7・8(編集 primitive)が前提にしている「自分で `replace()` した1本の編集系譜」ではなく、すでに存在する2つの source を外から渡されて比較する点がシナリオA〜Dと異なる。

1. 2つの source からそれぞれ木を作る(すでに独立に parse 済みでもよい)
2. node 単位で added / removed / unchanged を得る
3. 将来的には、rename / move / modify のような、より意味のある対応付け(GumTree のような tree edit distance アルゴリズムによる node matching)まで区別したい。v1 時点では、そこまでは見送る(下記「操作13」参照)

## 操作リスト

シナリオから導出した、Astars core が支えるべき操作(`ACTION_ITEMS.ja.md` の「強みの実現状況」と対応)。

### v0 で実装済み

1. 親子ナビゲーション(parent / children)
2. traverse — 木全体を辿る(`walk`、kind filter あり)
3. `find(kind)`
4. `node_at(byte_offset)` — 位置 → node
5. `span_of(node)` — node → byte 範囲
6. `source_of(node)` — node → source のslice

### v1 で実装済み

7. **編集 primitive**: `SyntaxTree::replace` — source の一部を書き換えて新しい tree/source を作る。8・9 が成立する前提
8. **編集前後の node 同一性比較**: `SyntaxTree::unchanged_in` — このnodeは編集で変わっていないか(シナリオA・D)
11. **部分木の一括 export**: `SyntaxTree::dump` — node 一個ずつではなく、subtree をまとめて1回の FFI 呼び出しで取り出す(シナリオC・D。FFI 越しの逐次呼び出しは呼び出し回数分のオーバーヘッドが乗る)

### 未実装(Not Now。具体的な消費者が出てくるまで着手しない)

9. **派生系譜の追跡**: この variant node は元のどの node から来たか(シナリオB で必須)
10. **名前/kind ベースのアドレス指定**: byte offset とは別の軸で node を引く(シナリオA の核心。現状は `find(kind)` で候補を絞ってから利用者側で名前を確認する形に留まる)

### 計画中(v1/v2 の二段階で進める)

13. **独立な2木の構造的 diff**(シナリオE): `tree.edit()` 系譜で繋がっていない2つの source を比較し、node 単位で added/removed/unchanged を得る
    - **v1(暫定)**: 2つの source のテキスト diff(Myers diff)を `InputEdit` の列に変換し、`tree.edit()` + `changed_ranges()` という既存の編集 primitive の仕組みに乗せて実現する。node の対応付けは行わず、`changed_ranges` との byte span overlap だけで判定する(overlap すれば旧木側は removed、新木側は added。重ならなければ unchanged)。rename/move/modify の区別はできない
    - **v2(最終形態)**: GumTree のような tree edit distance アルゴリズムで node 同士を対応付け、modified/moved/renamed まで区別できるようにする。v1 は、この v2 に置き換えるまでの代替実装と位置づける

### 制約(機能要求ではなく、全操作に効いてくる前提)

12. node は binding(Python/Node)に **値として** 渡せる必要がある。Rust の参照・lifetime を FFI 境界の外に持ち出せない — v0/v1 とも `NodeId(u32)` で満たしている

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

## データ構造設計の Open Questions(解決済み)

- ~~AST node を arena(index 参照)で持つか~~ → arena + `NodeId(u32)` で決定・実装済み([ARCHITECTURE.ja.md](ARCHITECTURE.ja.md) の「astars-core」クラス図)
- Piece Table の具体的な実装 → v1 編集 primitive では見送り(下記)。導入時期は再検討
- 操作9(系譜追跡)の台帳をどこに持つか → 未着手。v1 編集 primitive のスコープ外(下記)
- 操作10(名前/kind アドレス指定)を tree-sitter query 言語の上に作るか、自前 traversal で作るか → 未着手
- 操作11(部分木の一括 export)の具体的な API 形状 → `dump(id) -> Vec<NodeInfo>` 形式で実装済み([ARCHITECTURE.ja.md](ARCHITECTURE.ja.md) の「bindings/python」/「bindings/node」クラス図)

## 編集 primitive(v1)の設計

### きっかけ

AWS が Kiro IDE 向けに AST ベースの構造化編集(`insert_node` / `replace_node` / `delete_node` / `replace_in_node`、名前/kind セレクタ)を公開し、LLM 呼び出し数・token 数・ツールエラー率で実測の効果を示した([参考](https://aws.amazon.com/jp/blogs/news/surgical-precision-with-ast/))。これはシナリオA の仮説(diff/行番号より名前/kind アドレス指定が LLM agent に向く)の裏付けになる一方、「名前/kind ベースの構造化編集」という方向性自体は先に製品化されつつある。

ただし Kiro は特定 IDE に閉じた内製機能であり、(1) 複数ランタイム(Python/Node)から同じ engine を再利用できること、(2) 編集を「適用して終わり」ではなく「結果を解析する」loop の一部として扱うこと、の2点は Astars 固有の強みとして残る。v1 の編集 primitive は、単体の `insert`/`replace`/`delete` ではなく、**編集(操作7)と編集前後比較(操作8)をセットで、Python/Node 両方に公開する**ことをゴールにする。

### 決定事項

1. **`SyntaxTree` に `Lang` を持たせる**: 編集後に再 parse するには言語を知っている必要があるが、現状 `Lang` は `ParseResult`/binding 側にしかない。`SyntaxTree` 自身に持たせる
2. **`replace(target, new_text) -> EditResult` を最小の編集 primitive にする**: insert/delete は「空文字列への置換」「zero-width span への置換」として `replace` 1本で表現し、v1 では `insert`/`delete` を別メソッドとして増やさない
3. **比較は `NodeId` の一致ではなく `changed_ranges` との byte 範囲重なりで行う**: 編集後の新しい木は別 arena なので、旧木の `NodeId` と新木の `NodeId` は番号として対応しない。`tree_sitter::Tree::changed_ranges(&old_raw, &new_raw)` が返す「変更された byte 範囲」に、旧 node の span が重ならなければ「変わっていない」と判定する

   ```rust
   pub struct EditResult {
       pub tree: SyntaxTree,           // 新しい木
       changed_ranges: Vec<ByteSpan>,  // private
   }

   impl SyntaxTree {
       pub fn replace(&self, target: NodeId, new_text: &str) -> EditResult;
       // id は self(旧木)の NodeId。edit.tree 側の NodeId ではない
       pub fn unchanged_in(&self, id: NodeId, edit: &EditResult) -> bool;
   }
   ```

4. **v1 は Piece Table なしの素朴な実装にする**: `source[..start] + new_text + source[end..]` で新しい source bytes を作り、`tree.edit(InputEdit)` + `parser.parse_with(callback, Some(&old_raw))` で incremental re-parse する(「決定した運用規約」の経路B)。効率化(Piece Table 化)は後回し

### v1 のスコープ外

- Piece Table によるテキスト格納の効率化
- 操作9(系譜追跡): 複数 variant を生成するパイプライン(シナリオB)向けの台帳。v1 は単発の `replace` 呼び出しに閉じる
- 操作10(名前/kind アドレス指定): v1 は呼び出し側が `find(kind)` 等で `target: NodeId` を解決してから `replace` を呼ぶ前提。「関数名で直接引く」until 便利 API は次の increment
- `insert`/`delete` 専用メソッド

## Next Step

上記の決定を元に、クラス図(`EditResult` と `SyntaxTree` の関係)とシーケンス図(`replace` 呼び出し時の処理の流れ: source 書き換え → `tree.edit()` → re-parse → `changed_ranges` 取得)を作り、実装に進む。

## 構造的 diff(操作13)の設計(計画中)

### きっかけ

AST を自在に操れることの延長として、「同じファイルの独立な2バージョン(git の前後コミットなど)を構造的に比較したい」という要望が出た。`replace`/`unchanged_in` は自分で `tree.edit()` した1本の編集系譜の中でしか機能しないため、外から渡された2つの独立な source を比較する用途(シナリオE、`astars-code-review` の土台)には対応できない。

最終的には GumTree のような tree edit distance アルゴリズムで node を対応付け、rename/move/modify まで区別できる状態を目指す。ただし GumTree 相当の実装は規模が大きいため、それまでの代替として、既存の編集 primitive の仕組みに乗せた簡易版を v1 として先に用意する。

### 決定事項(現時点の方針。実装時に確定)

1. **2つの source のテキスト diff を `InputEdit` の列に変換し、既存の `tree.edit()` + `changed_ranges()` の仕組みに乗せる**: `replace` が単一 span の書き換えから `InputEdit` を1つ作るのに対し、diff は複数 hunk から複数の `InputEdit` を作る。tree-sitter への適用順序(末尾側から適用しないと後続の byte offset がずれる)に注意が必要
2. **テキスト diff 自体は自前実装しない**: Myers diff を手で書くのは避け、`similar` のような実績のある軽量 crate に任せる
3. **戻り値は `EditResult` と同じ形にする**: `tree`(新しい木)+ private な `changed_ranges` を持つ型にし、`unchanged_in` をそのまま(あるいはごく小さな追加で)再利用できるようにする
4. **node 単位の分類は byte span の overlap 判定のみ**: `changed_ranges` と重ならなければ `Unchanged`。旧木側で重なれば `Removed`、新木側で重なれば `Added` とする。node 同士の対応付け(「この関数は名前を変えて残っている」等)は行わない — それは v2(GumTree)の仕事

### v1 のスコープ外(v2 = GumTree 導入まで見送り)

- GumTree のような tree edit distance による node matching
- `Modified` / `Moved` / `Renamed` の区別(v1 は `Added`/`Removed`/`Unchanged` の3値のみ)
- 複数言語をまたいだ diff(v0 scope と同じく Python のみ)

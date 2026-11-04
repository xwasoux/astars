# Source Model: 文字列・座標・diagnostics の設計根拠

関連文書:

- [../strategy/STRATEGY.ja.md](../strategy/STRATEGY.ja.md)
- [ARCHITECTURE.ja.md](ARCHITECTURE.ja.md)
- [NODE_RESOLUTION.ja.md](NODE_RESOLUTION.ja.md)

`SyntaxTree` が source をどう保持し、どう座標・診断情報に変換するかに関する設計判断。

## 文字列は lossy に decode する(`errors=replace` 相当)

`parse_bytes` は非 UTF-8 の source もそのまま受け付ける。`span_of`/`node_at` はバイト列を直接扱うため offset は常に正しいが、`source_of` で文字列として取り出す際は `String::from_utf8_lossy`(不正な UTF-8 は U+FFFD になる)を使い、panic しない。`parse_file` は `encoding_rs` が decode 結果を Rust の `String` として返すため、宣言した encoding 内で不正なバイト列がある場合を除き、常に valid UTF-8 になる。

## `Point.column` は byte column(Unicode code point / grapheme ではない)

`point_at` が返す `Point` の `column` は 0-based の byte column である。`ByteSpan` と一貫させるためで、`ByteSpan` は `Copy` かつ `span_of`/`EditResult.changed_ranges` の overlap 判定などホットパスで使われる一方、`Point` は必要な時だけ `line_col_at` で計算する。grapheme-aware な column が必要な消費者が具体的に出るまでは対応しない。

## Diagnostics は tree-sitter の `ERROR`/`MISSING` node から直接読む

`diagnostics()` は `self.raw`(tree-sitter の木)を直接 preorder で辿って `ERROR`/`MISSING` node を集める。`SyntaxNode` の arena を経由しないのは、recovery node が tree-sitter 固有の概念であり `SyntaxNode` がそれを記録しないため。v0 では `Diagnostic::Error` のみを生成する(tree-sitter の recovery node は常に error)が、将来 `Warning` を API を壊さずに追加できるよう、severity は enum にしている。

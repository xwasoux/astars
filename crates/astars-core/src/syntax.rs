//! `SyntaxTree` / `SyntaxNode`: the v0 program-structure type.
//!
//! See `docs/architecture/syntax-tree-structure.drawio.svg` for the class
//! diagram this module implements, and `docs/architecture/EDIT_MODEL.ja.md`
//! for why the design looks the way it does.
//!
//! v0 note: a `SyntaxNode` is tree-sitter's raw CST node, 1:1 - there is no
//! rule-based normalization yet (that would be a future `AstNode` layer on
//! top). `span` lives directly on the node because v0 has no many-to-many
//! raw-origin mapping need; if normalization is added later, that is when a
//! `SyntaxGraph`-style indirection would come back.
//!
//! `replace` / `EditResult` / `unchanged_in` are the v1 edit primitive (see
//! EDIT_MODEL.ja.md's "編集 primitive(v1)の設計"). v1 is deliberately naive:
//! source bytes are spliced with a plain copy (no Piece Table yet), and
//! "did this node change" is answered via `tree_sitter::Tree::changed_ranges`
//! rather than any `NodeId` bookkeeping across trees - a `NodeId` from the
//! old tree and a `NodeId` from the new tree are indices into two different
//! arenas and are never comparable directly.

use crate::Lang;

/// Index into a `SyntaxTree`'s arena. Cheap to copy, safe to hand across the
/// FFI boundary to bindings (constraint 12 in EDIT_MODEL.ja.md) - unlike a
/// borrowed `&SyntaxNode`, it has no lifetime tied to the tree.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct NodeId(u32);

impl NodeId {
    /// Escape hatch for binding crates, which can only pass plain integers
    /// across FFI (constraint 12 in EDIT_MODEL.ja.md) and need to round-trip
    /// them back into `NodeId` to call `SyntaxTree` methods.
    pub fn as_u32(self) -> u32 {
        self.0
    }

    /// Inverse of `as_u32`. A `NodeId` built this way is only meaningful for
    /// the `SyntaxTree` it came from; passing an out-of-range value makes
    /// `SyntaxTree` methods panic (bindings catch this as an exception - see
    /// `docs/architecture/python-tree-binding.drawio.svg` /
    /// `node-tree-binding.drawio.svg`).
    pub fn from_u32(value: u32) -> Self {
        NodeId(value)
    }
}

/// A byte range into the source, half-open `[start_byte, end_byte)`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ByteSpan {
    pub start_byte: usize,
    pub end_byte: usize,
}

#[derive(Debug, Clone)]
struct SyntaxNode {
    // tree_sitter::Node::kind() is tied to the tree's lifetime, not actually
    // 'static, so this is owned rather than borrowed (see EDIT_MODEL.ja.md /
    // the diagram for the original &'static str plan - this is a deviation).
    kind: String,
    field_name: Option<String>,
    span: ByteSpan,
    parent: Option<NodeId>,
    children: Vec<NodeId>,
}

/// Parse result's normalized structure: an arena of `SyntaxNode`, plus enough
/// of the original parse to support future incremental edits.
///
/// `Clone` (`tree_sitter::Tree` is itself `Clone`, structurally shared) is
/// needed by binding crates: `EditResult.tree` can only be read out once
/// through `&EditResult` without consuming it, since `changed_ranges` stays
/// private and binding wrappers must keep the whole `EditResult` alive to
/// answer `unchanged_in` later.
#[derive(Clone)]
pub struct SyntaxTree {
    nodes: Vec<SyntaxNode>,
    root: NodeId,
    source: Vec<u8>,
    // Kept so the edit primitive can do `raw.edit(...)` +
    // `parser.parse(..., Some(&raw))` (EDIT_MODEL.ja.md's edit policy)
    // instead of an unrelated from-scratch re-parse. Never exposed publicly:
    // SyntaxNode itself holds no tree-sitter type, so this stays an
    // implementation detail of SyntaxTree alone.
    raw: tree_sitter::Tree,
    // Needed to build a parser for re-parsing after an edit - SyntaxTree
    // only remembers the language, not a ready `tree_sitter::Parser`.
    lang: Lang,
}

impl SyntaxTree {
    pub(crate) fn from_tree_sitter(lang: Lang, raw: tree_sitter::Tree, source: Vec<u8>) -> Self {
        let mut nodes = Vec::new();
        let root = Self::build_node(raw.root_node(), None, None, &mut nodes);
        Self { nodes, root, source, raw, lang }
    }

    fn build_node(
        ts_node: tree_sitter::Node,
        parent: Option<NodeId>,
        field_name: Option<&str>,
        nodes: &mut Vec<SyntaxNode>,
    ) -> NodeId {
        let my_id = NodeId(nodes.len() as u32);
        nodes.push(SyntaxNode {
            kind: ts_node.kind().to_string(),
            field_name: field_name.map(str::to_string),
            span: ByteSpan {
                start_byte: ts_node.start_byte(),
                end_byte: ts_node.end_byte(),
            },
            parent,
            children: Vec::new(),
        });

        let mut children = Vec::new();
        let mut cursor = ts_node.walk();
        if cursor.goto_first_child() {
            loop {
                let child_field_name = cursor.field_name();
                let child_id = Self::build_node(cursor.node(), Some(my_id), child_field_name, nodes);
                children.push(child_id);
                if !cursor.goto_next_sibling() {
                    break;
                }
            }
        }
        nodes[my_id.0 as usize].children = children;

        my_id
    }

    /// Preorder traversal of the whole tree, starting at the root.
    pub fn walk(&self) -> impl Iterator<Item = NodeId> + '_ {
        Preorder { tree: self, stack: vec![self.root] }
    }

    /// All nodes whose tree-sitter kind equals `kind`, in preorder.
    pub fn find(&self, kind: &str) -> Vec<NodeId> {
        self.walk().filter(|id| self.node(*id).kind == kind).collect()
    }

    /// The most specific node covering `offset`, or `None` if `offset` is at
    /// or past the end of the source (half-open spans: EOF is never "inside").
    pub fn node_at(&self, offset: usize) -> Option<NodeId> {
        if !self.span_contains(self.root, offset) {
            return None;
        }
        let mut current = self.root;
        loop {
            let next = self
                .node(current)
                .children
                .iter()
                .copied()
                .find(|&child| self.span_contains(child, offset));
            match next {
                Some(child) => current = child,
                None => return Some(current),
            }
        }
    }

    pub fn span_of(&self, id: NodeId) -> ByteSpan {
        self.node(id).span
    }

    pub fn source_of(&self, id: NodeId) -> &str {
        let span = self.span_of(id);
        std::str::from_utf8(&self.source[span.start_byte..span.end_byte])
            .expect("astars-core: node span was not on a UTF-8 boundary")
    }

    pub fn root(&self) -> NodeId {
        self.root
    }

    pub fn lang(&self) -> Lang {
        self.lang
    }

    pub fn kind_of(&self, id: NodeId) -> &str {
        &self.node(id).kind
    }

    pub fn field_name_of(&self, id: NodeId) -> Option<&str> {
        self.node(id).field_name.as_deref()
    }

    pub fn parent_of(&self, id: NodeId) -> Option<NodeId> {
        self.node(id).parent
    }

    pub fn children_of(&self, id: NodeId) -> &[NodeId] {
        &self.node(id).children
    }

    /// Replace `target`'s source span with `new_text`, producing a new tree.
    /// `self` is untouched (immutable edit) - see EDIT_MODEL.ja.md's "編集
    /// primitive(v1)の設計". insert/delete are expressed as `replace` with
    /// an empty `target` span or an empty `new_text`, respectively; v1 does
    /// not add separate methods for them.
    ///
    /// Follows the decided edit policy: splice the source (v1: plain copy,
    /// no Piece Table yet), tell tree-sitter what changed via
    /// `tree.edit(InputEdit)`, then re-parse with the edited old tree passed
    /// in so unaffected subtrees are reused and `changed_ranges` becomes
    /// available.
    pub fn replace(&self, target: NodeId, new_text: &str) -> EditResult {
        let span = self.span_of(target);

        let mut new_source =
            Vec::with_capacity(self.source.len() - (span.end_byte - span.start_byte) + new_text.len());
        new_source.extend_from_slice(&self.source[..span.start_byte]);
        new_source.extend_from_slice(new_text.as_bytes());
        new_source.extend_from_slice(&self.source[span.end_byte..]);

        let new_end_byte = span.start_byte + new_text.len();
        let start_position = point_at(&self.source, span.start_byte);
        let old_end_position = point_at(&self.source, span.end_byte);
        let new_end_position = end_position_after_insert(start_position, new_text);

        let mut edited_raw = self.raw.clone();
        edited_raw.edit(&tree_sitter::InputEdit {
            start_byte: span.start_byte,
            old_end_byte: span.end_byte,
            new_end_byte,
            start_position,
            old_end_position,
            new_end_position,
        });

        let mut parser = crate::parse::parser_for(self.lang);
        let new_raw = parser
            .parse(&new_source, Some(&edited_raw))
            .expect("astars-core: re-parse after edit failed");

        let changed_ranges = edited_raw
            .changed_ranges(&new_raw)
            .map(|r| ByteSpan {
                start_byte: r.start_byte,
                end_byte: r.end_byte,
            })
            .collect();

        EditResult {
            tree: SyntaxTree::from_tree_sitter(self.lang, new_raw, new_source),
            changed_ranges,
        }
    }

    /// Did `id` (a node in `self`, the tree *before* `edit`) survive into
    /// `edit.tree` unchanged? Answered via byte-range overlap against
    /// `edit`'s `changed_ranges`, not `NodeId` equality - a `NodeId` in
    /// `self` and a `NodeId` in `edit.tree` index two different arenas and
    /// are never comparable directly (see the module-level doc comment).
    pub fn unchanged_in(&self, id: NodeId, edit: &EditResult) -> bool {
        let span = self.span_of(id);
        !edit
            .changed_ranges
            .iter()
            .any(|changed| spans_overlap(span, *changed))
    }

    fn node(&self, id: NodeId) -> &SyntaxNode {
        &self.nodes[id.0 as usize]
    }

    fn span_contains(&self, id: NodeId, offset: usize) -> bool {
        let span = self.node(id).span;
        span.start_byte <= offset && offset < span.end_byte
    }
}

/// The result of `SyntaxTree::replace`: the new tree, plus enough to answer
/// `unchanged_in` queries against the tree the edit started from.
pub struct EditResult {
    pub tree: SyntaxTree,
    changed_ranges: Vec<ByteSpan>,
}

fn spans_overlap(a: ByteSpan, b: ByteSpan) -> bool {
    a.start_byte < b.end_byte && b.start_byte < a.end_byte
}

/// `tree_sitter::Point` (row, column) for a byte offset into `source`. v1
/// scans linearly - fine for a single edit call, not optimized for repeated
/// use (see EDIT_MODEL.ja.md: Piece Table work is deferred, not v1 scope).
fn point_at(source: &[u8], byte_offset: usize) -> tree_sitter::Point {
    let mut row = 0;
    let mut line_start = 0;
    for (i, &b) in source[..byte_offset].iter().enumerate() {
        if b == b'\n' {
            row += 1;
            line_start = i + 1;
        }
    }
    tree_sitter::Point {
        row,
        column: byte_offset - line_start,
    }
}

/// The `Point` reached after inserting `text` starting at `start`.
fn end_position_after_insert(start: tree_sitter::Point, text: &str) -> tree_sitter::Point {
    let bytes = text.as_bytes();
    match bytes.iter().rposition(|&b| b == b'\n') {
        None => tree_sitter::Point {
            row: start.row,
            column: start.column + bytes.len(),
        },
        Some(last_newline) => tree_sitter::Point {
            row: start.row + bytes.iter().filter(|&&b| b == b'\n').count(),
            column: bytes.len() - (last_newline + 1),
        },
    }
}

impl std::fmt::Debug for SyntaxTree {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SyntaxTree")
            .field("root", &self.root)
            .field("node_count", &self.nodes.len())
            .finish()
    }
}

struct Preorder<'a> {
    tree: &'a SyntaxTree,
    stack: Vec<NodeId>,
}

impl Iterator for Preorder<'_> {
    type Item = NodeId;

    fn next(&mut self) -> Option<NodeId> {
        let id = self.stack.pop()?;
        for &child in self.tree.node(id).children.iter().rev() {
            self.stack.push(child);
        }
        Some(id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{parse_str, Lang};

    #[test]
    fn walk_visits_every_node_in_preorder_and_root_first() {
        let tree = parse_str("x = 1\n", Lang::Python).tree;
        let ids: Vec<NodeId> = tree.walk().collect();
        assert_eq!(ids.first(), Some(&tree.root));
        assert_eq!(ids.len(), tree.nodes.len());
    }

    #[test]
    fn find_returns_nodes_matching_kind() {
        let tree = parse_str("def hello():\n    return 1\n", Lang::Python).tree;
        let defs = tree.find("function_definition");
        assert_eq!(defs.len(), 1);
    }

    #[test]
    fn node_at_returns_most_specific_node() {
        let tree = parse_str("x = 1\n", Lang::Python).tree;
        let id = tree.node_at(0).expect("offset 0 should be inside the module");
        // the most specific node at offset 0 should not be the whole module
        assert_ne!(tree.span_of(id), tree.span_of(tree.root));
    }

    #[test]
    fn node_at_returns_none_at_eof() {
        let source = "x = 1\n";
        let tree = parse_str(source, Lang::Python).tree;
        assert_eq!(tree.node_at(source.len()), None);
    }

    #[test]
    fn span_of_and_source_of_round_trip() {
        let source = "def hello():\n    return 1\n";
        let tree = parse_str(source, Lang::Python).tree;
        let id = tree.find("function_definition")[0];
        let span = tree.span_of(id);
        assert_eq!(&source[span.start_byte..span.end_byte], tree.source_of(id));
    }

    #[test]
    fn replace_updates_source_and_reports_correct_changed_status() {
        let source = "x = 1\ny = 2\n";
        let tree = parse_str(source, Lang::Python).tree;
        let assignments = tree.find("assignment");
        assert_eq!(assignments.len(), 2);
        let (first, second) = (assignments[0], assignments[1]);

        let edit = tree.replace(first, "x = 99");

        let new_assignments = edit.tree.find("assignment");
        assert_eq!(new_assignments.len(), 2);
        assert_eq!(edit.tree.source_of(new_assignments[0]), "x = 99");
        assert_eq!(edit.tree.source_of(new_assignments[1]), "y = 2");

        // the untouched statement survives; the edited one does not
        assert!(tree.unchanged_in(second, &edit));
        assert!(!tree.unchanged_in(first, &edit));
    }

    #[test]
    fn replace_with_multiline_text_reparses_correctly() {
        // regression test for end_position_after_insert: inserted text with
        // embedded newlines must not corrupt what follows it
        let source = "x = 1\ny = 2\n";
        let tree = parse_str(source, Lang::Python).tree;
        let first = tree.find("assignment")[0];

        let edit = tree.replace(first, "x = (\n    1 + 1\n)");
        assert_eq!(
            edit.tree.source_of(edit.tree.root()),
            "x = (\n    1 + 1\n)\ny = 2\n"
        );
        assert_eq!(edit.tree.find("assignment").len(), 2);
    }

    #[test]
    fn replace_can_delete_by_using_empty_text() {
        let source = "x = 1\ny = 2\n";
        let tree = parse_str(source, Lang::Python).tree;
        let first = tree.find("assignment")[0];

        let edit = tree.replace(first, "");

        // Note: tree-sitter-python's `module` node excludes a leading blank
        // line from its span, so `source_of(root())` is "y = 2\n" here, not
        // the full "\ny = 2\n" buffer - `source_of(root)` is not guaranteed
        // to cover 100% of the source when there is leading/trailing trivia.
        let remaining = edit.tree.find("assignment");
        assert_eq!(remaining.len(), 1);
        assert_eq!(edit.tree.source_of(remaining[0]), "y = 2");
    }
}


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

#[derive(Debug)]
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
pub struct SyntaxTree {
    nodes: Vec<SyntaxNode>,
    root: NodeId,
    source: Vec<u8>,
    // Kept only so a future edit primitive can do `raw.edit(...)` +
    // `parser.parse_with(..., Some(&raw))` (EDIT_MODEL.ja.md's edit policy)
    // instead of an unrelated from-scratch re-parse. Never exposed publicly:
    // SyntaxNode itself holds no tree-sitter type, so this stays an
    // implementation detail of SyntaxTree alone.
    #[allow(dead_code)] // not read until the edit primitive lands
    raw: tree_sitter::Tree,
}

impl SyntaxTree {
    pub(crate) fn from_tree_sitter(raw: tree_sitter::Tree, source: Vec<u8>) -> Self {
        let mut nodes = Vec::new();
        let root = Self::build_node(raw.root_node(), None, None, &mut nodes);
        Self { nodes, root, source, raw }
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

    fn node(&self, id: NodeId) -> &SyntaxNode {
        &self.nodes[id.0 as usize]
    }

    fn span_contains(&self, id: NodeId, offset: usize) -> bool {
        let span = self.node(id).span;
        span.start_byte <= offset && offset < span.end_byte
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
}

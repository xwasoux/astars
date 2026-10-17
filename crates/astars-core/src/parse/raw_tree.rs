//! `RawTree`: internal wrapper around a tree-sitter parse tree.
//!
//! Not exported outside the `parse` module - see `docs/architecture/core-parse-spike.drawio.svg`
//! ("Parser は交換可能であるべき": tree_sitter types stay confined to `parse`, never
//! appear in `astars_core`'s public surface).

pub(crate) struct RawTree {
    inner: tree_sitter::Tree,
    #[allow(dead_code)] // kept for the next iteration (span/source slicing)
    source: Vec<u8>,
}

impl RawTree {
    pub(crate) fn new(inner: tree_sitter::Tree, source: Vec<u8>) -> Self {
        Self { inner, source }
    }

    pub(crate) fn node_count(&self) -> usize {
        count_nodes(self.inner.root_node())
    }
}

fn count_nodes(node: tree_sitter::Node) -> usize {
    let mut cursor = node.walk();
    let mut count = 1;
    for child in node.children(&mut cursor) {
        count += count_nodes(child);
    }
    count
}

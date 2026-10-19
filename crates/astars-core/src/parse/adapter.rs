//! `ParseAdapter`: the only place in this crate allowed to touch tree-sitter's
//! parser API directly - see `docs/architecture/syntax-tree-structure.drawio.svg`.
//!
//! Its job stops at "parse". Turning the resulting `tree_sitter::Tree` into
//! our own arena (`SyntaxTree`) is `SyntaxTree`'s job, not this module's -
//! that conversion needs access to `SyntaxTree`'s private fields.

use crate::syntax::SyntaxTree;
use crate::Lang;

pub(crate) struct ParseAdapter;

impl ParseAdapter {
    pub(crate) fn parse(source: &str, lang: Lang) -> SyntaxTree {
        let language = match lang {
            Lang::Python => tree_sitter_python::LANGUAGE.into(),
        };

        let mut parser = tree_sitter::Parser::new();
        parser
            .set_language(&language)
            .expect("astars-core: failed to load tree-sitter grammar");

        let source_bytes = source.as_bytes().to_vec();
        let tree = parser
            .parse(&source_bytes, None)
            .expect("astars-core: tree-sitter returned no tree");

        SyntaxTree::from_tree_sitter(tree, source_bytes)
    }
}

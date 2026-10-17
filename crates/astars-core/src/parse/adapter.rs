//! `ParseAdapter`: the only place in this crate allowed to touch tree-sitter's
//! parser API directly - see `docs/architecture/core-parse-spike.drawio.svg`.

use super::raw_tree::RawTree;
use crate::Lang;

pub(crate) struct ParseAdapter;

impl ParseAdapter {
    pub(crate) fn parse(source: &str, lang: Lang) -> RawTree {
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

        RawTree::new(tree, source_bytes)
    }
}

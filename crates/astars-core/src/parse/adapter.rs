//! `ParseAdapter`: the only place in this crate allowed to touch tree-sitter's
//! parser API directly - see the "astars-core" class diagram in
//! `docs/architecture/ARCHITECTURE.ja.md`.
//!
//! Its job stops at "parse". Turning the resulting `tree_sitter::Tree` into
//! our own arena (`SyntaxTree`) is `SyntaxTree`'s job, not this module's -
//! that conversion needs access to `SyntaxTree`'s private fields.

use crate::syntax::SyntaxTree;
use crate::Lang;

pub(crate) struct ParseAdapter;

impl ParseAdapter {
    /// Parses raw bytes directly - `source` need not be valid UTF-8 (that is
    /// `parse_bytes`'s whole point; `parse_str` just hands in `str::as_bytes()`,
    /// which always is).
    pub(crate) fn parse(source: &[u8], lang: Lang) -> SyntaxTree {
        let mut parser = parser_for(lang);
        let tree = parser
            .parse(source, None)
            .expect("astars-core: tree-sitter returned no tree");

        SyntaxTree::from_tree_sitter(lang, tree, source.to_vec())
    }
}

/// Build a `tree_sitter::Parser` configured for `lang`. Exposed to `syntax`
/// (not just used internally by `ParseAdapter::parse`) because the edit
/// primitive needs to re-parse with the same language after `tree.edit()`
/// (EDIT_MODEL.ja.md's edit policy) - `SyntaxTree` only remembers `Lang`,
/// not a ready-to-use parser.
pub(crate) fn parser_for(lang: Lang) -> tree_sitter::Parser {
    let language = match lang {
        Lang::Python => tree_sitter_python::LANGUAGE.into(),
    };

    let mut parser = tree_sitter::Parser::new();
    parser
        .set_language(&language)
        .expect("astars-core: failed to load tree-sitter grammar");
    parser
}

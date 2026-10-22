//! Astars core engine: parse / normalize / map / query / edit.
//!
//! This crate's public surface is `Lang`, `ParseResult`, `SyntaxTree` (+
//! `NodeId`, `ByteSpan`, `EditResult`), and `parse_str` - see
//! `docs/architecture/syntax-tree-structure.drawio.svg` for the class diagram
//! this module implements, and `docs/STRATEGY.ja.md` for the design bets it
//! must honor: parser-isolated (no tree_sitter types in the public surface),
//! binding-agnostic (no pyo3/napi-rs dependency in this crate).

mod parse;
mod syntax;

pub use syntax::{ByteSpan, EditResult, NodeId, SyntaxTree};

use parse::ParseAdapter;

/// Source language to parse. Python is the only reference-path variant for now;
/// see `STRATEGY.ja.md` ("Python を対象言語の Reference Path にする").
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Lang {
    Python,
}

/// Normalized parse output.
#[derive(Debug)]
pub struct ParseResult {
    pub lang: Lang,
    pub tree: SyntaxTree,
}

/// Parse `source` as `lang` and return a normalized, parser-agnostic result.
/// This is the only entry point `astars-core` exposes for this spike.
pub fn parse_str(source: &str, lang: Lang) -> ParseResult {
    let tree = ParseAdapter::parse(source, lang);
    ParseResult { lang, tree }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_python_source_and_builds_a_tree() {
        let result = parse_str("def hello():\n    return 1\n", Lang::Python);
        assert_eq!(result.lang, Lang::Python);
        assert!(result.tree.walk().count() > 0);
    }

    #[test]
    fn empty_source_still_parses() {
        let result = parse_str("", Lang::Python);
        assert_eq!(result.lang, Lang::Python);
        assert!(
            result.tree.walk().count() > 0,
            "tree-sitter always returns at least a root node"
        );
    }
}

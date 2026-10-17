//! Astars core engine: parse / normalize / map / query / edit.
//!
//! This crate's public surface is intentionally tiny right now (`Lang`,
//! `ParseResult`, `parse_str`) - see `docs/architecture/core-parse-spike.drawio.svg`
//! for the class diagram this module implements, and `docs/STRATEGY.ja.md` for
//! the design bets it must honor: parser-isolated (no tree_sitter types appear
//! here), binding-agnostic (no pyo3/napi-rs dependency in this crate).

mod parse;

use parse::ParseAdapter;

/// Source language to parse. Python is the only reference-path variant for now;
/// see `STRATEGY.ja.md` ("Python を対象言語の Reference Path にする").
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Lang {
    Python,
}

/// Normalized parse output. Deliberately minimal for this first spike - AST /
/// SyntaxGraph equivalents are modeled in a later iteration (see the diagram's
/// design notes).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ParseResult {
    pub lang: Lang,
    pub node_count: usize,
}

/// Parse `source` as `lang` and return a normalized, parser-agnostic result.
/// This is the only entry point `astars-core` exposes for this spike.
pub fn parse_str(source: &str, lang: Lang) -> ParseResult {
    let raw_tree = ParseAdapter::parse(source, lang);
    ParseResult {
        lang,
        node_count: raw_tree.node_count(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_python_source_and_counts_nodes() {
        let result = parse_str("def hello():\n    return 1\n", Lang::Python);
        assert_eq!(result.lang, Lang::Python);
        assert!(result.node_count > 0);
    }

    #[test]
    fn empty_source_still_parses() {
        let result = parse_str("", Lang::Python);
        assert_eq!(result.lang, Lang::Python);
        assert!(result.node_count > 0, "tree-sitter always returns at least a root node");
    }
}

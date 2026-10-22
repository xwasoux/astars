//! Parser-recovery diagnostics: tree-sitter's `ERROR` / `MISSING` nodes,
//! normalized into a parser-agnostic shape. Ports the behavior documented in
//! `docs/SOURCE_MAPPING_PLAN.ja.md` ("Diagnostics Span") from the Python
//! prototype's `Diagnostic` / `_diagnostics_from_tree`.

use crate::syntax::ByteSpan;

/// v0 only ever produces `Error` (tree-sitter's recovery nodes are always
/// errors) - the variant exists so callers match on a type, not a bare
/// string, and so a future `Warning` can be added without an API break.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Severity {
    Error,
}

/// One parser-recovery diagnostic: an `ERROR` or `MISSING` node tree-sitter
/// produced while parsing, translated to a byte span. Unlike the Python
/// prototype's `Diagnostic.span: Optional[SourceSpan]`, `span` is not
/// optional here - v0's only diagnostic source is tree-sitter's recovery
/// nodes, which always carry a real span.
#[derive(Debug, Clone)]
pub struct Diagnostic {
    pub severity: Severity,
    pub message: String,
    pub span: ByteSpan,
}

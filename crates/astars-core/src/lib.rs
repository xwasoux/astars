//! Astars core engine: parse / normalize / map / query / edit.
//!
//! This crate's public surface is `Lang`, `ParseResult`, `SyntaxTree` (+
//! `NodeId`, `ByteSpan`, `Point`, `EditResult`, `Diagnostic`, `Severity`), and
//! `parse_str` / `parse_bytes` / `parse_file` - see the "astars-core" class
//! diagram in `docs/architecture/ARCHITECTURE.ja.md` for the design this
//! module implements, and `docs/STRATEGY.ja.md` for the design bets it
//! must honor: parser-isolated (no tree_sitter types in the public surface),
//! binding-agnostic (no pyo3/napi-rs dependency in this crate).

mod diagnostics;
mod parse;
mod syntax;

pub use diagnostics::{Diagnostic, Severity};
pub use syntax::{ByteSpan, EditResult, NodeId, Point, SyntaxTree};

use parse::ParseAdapter;
use std::path::Path;

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

/// Errors `astars-core`'s public API can return.
#[derive(Debug)]
pub enum AstarsError {
    /// `parse_file` failed to read its path.
    Io(std::io::Error),
    /// `parse_file` was given an `encoding` label `encoding_rs::Encoding::for_label`
    /// does not recognize (the WHATWG Encoding Standard's labels, e.g. `"utf-8"`,
    /// `"shift_jis"`, `"euc-jp"`).
    UnsupportedEncoding(String),
}

impl std::fmt::Display for AstarsError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AstarsError::Io(e) => write!(f, "astars-core: failed to read file: {e}"),
            AstarsError::UnsupportedEncoding(label) => {
                write!(f, "astars-core: unsupported encoding label: {label}")
            }
        }
    }
}

impl std::error::Error for AstarsError {}

/// Parse `source` as `lang` and return a normalized, parser-agnostic result.
pub fn parse_str(source: &str, lang: Lang) -> ParseResult {
    let tree = ParseAdapter::parse(source.as_bytes(), lang);
    ParseResult { lang, tree }
}

/// Parse raw bytes as `lang`. Unlike `parse_str`, `source` need not be valid
/// UTF-8 - invalid byte sequences surface as replacement characters when
/// read back via `SyntaxTree::source_of`, not as a parse failure (mirrors
/// the Python prototype's `errors="replace"` policy; see
/// `docs/SOURCE_MAPPING_PLAN.ja.md`'s "SourceUnit.source").
pub fn parse_bytes(source: &[u8], lang: Lang) -> ParseResult {
    let tree = ParseAdapter::parse(source, lang);
    ParseResult { lang, tree }
}

/// Read `path`, decode it as `encoding` (a WHATWG Encoding Standard label,
/// e.g. `"utf-8"`, `"shift_jis"`), and parse the result as `lang`. Decoding
/// an encoding other than UTF-8 always produces valid UTF-8 (`encoding_rs`
/// decodes straight into a Rust `String`), so the bytes `parse_bytes` sees
/// are always clean - unlike `parse_bytes` called directly, there is no
/// lossy replacement path here except for malformed byte sequences *within*
/// the declared encoding (mirrors the Python prototype's
/// `parse_file(..., encoding=...)`; see `docs/SOURCE_MAPPING_PLAN.ja.md`'s
/// "SourceUnit.source").
pub fn parse_file(path: &Path, lang: Lang, encoding: &str) -> Result<ParseResult, AstarsError> {
    let bytes = std::fs::read(path).map_err(AstarsError::Io)?;
    let encoding = encoding_rs::Encoding::for_label(encoding.as_bytes())
        .ok_or_else(|| AstarsError::UnsupportedEncoding(encoding.to_string()))?;
    let (decoded, _actual_encoding, _had_malformed_sequences) = encoding.decode(&bytes);
    Ok(parse_bytes(decoded.as_bytes(), lang))
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

    #[test]
    fn parse_bytes_matches_parse_str_for_valid_utf8() {
        let source = "x = 1\n";
        let from_str = parse_str(source, Lang::Python).tree;
        let from_bytes = parse_bytes(source.as_bytes(), Lang::Python).tree;
        assert_eq!(from_str.walk().count(), from_bytes.walk().count());
    }

    #[test]
    fn parse_bytes_handles_invalid_utf8_without_panicking() {
        // 0xFF is never valid as a UTF-8 lead byte - this must not panic
        // either while parsing or while reading the text back out.
        let source: &[u8] = b"x = 1\n\xFF\n";
        let result = parse_bytes(source, Lang::Python);
        let root = result.tree.root();
        assert!(result.tree.source_of(root).contains('\u{FFFD}'));
    }

    #[test]
    fn parse_file_reads_and_parses_the_file() {
        let dir = std::env::temp_dir();
        let path = dir.join(format!("astars-core-parse-file-test-{}.py", std::process::id()));
        std::fs::write(&path, "x = 1\n").unwrap();

        let result = parse_file(&path, Lang::Python, "utf-8").expect("parse_file should succeed");
        std::fs::remove_file(&path).unwrap();

        assert_eq!(result.lang, Lang::Python);
        assert!(result.tree.walk().count() > 0);
    }

    #[test]
    fn parse_file_reports_io_error_for_missing_path() {
        let path = std::env::temp_dir().join("astars-core-definitely-does-not-exist.py");
        let err = parse_file(&path, Lang::Python, "utf-8").expect_err("missing file should error");
        assert!(matches!(err, AstarsError::Io(_)));
    }

    #[test]
    fn parse_file_decodes_non_utf8_encoding() {
        // "x = 1  # こんにちは\n" encoded as Shift-JIS - a non-UTF-8 encoded
        // Python source file, as the "encoding" parameter is meant to handle.
        let (shift_jis_bytes, _, had_errors) =
            encoding_rs::SHIFT_JIS.encode("x = 1  # こんにちは\n");
        assert!(!had_errors, "test fixture text must be representable in Shift-JIS");

        let dir = std::env::temp_dir();
        let path = dir.join(format!("astars-core-parse-file-sjis-test-{}.py", std::process::id()));
        std::fs::write(&path, &shift_jis_bytes).unwrap();

        let result =
            parse_file(&path, Lang::Python, "shift_jis").expect("parse_file should succeed");
        std::fs::remove_file(&path).unwrap();

        let source = result.tree.source_of(result.tree.root());
        assert!(source.contains("こんにちは"));
    }

    #[test]
    fn parse_file_reports_error_for_unknown_encoding_label() {
        let dir = std::env::temp_dir();
        let path = dir.join(format!("astars-core-parse-file-badenc-test-{}.py", std::process::id()));
        std::fs::write(&path, "x = 1\n").unwrap();

        let err = parse_file(&path, Lang::Python, "not-a-real-encoding")
            .expect_err("unknown encoding label should error");
        std::fs::remove_file(&path).unwrap();

        assert!(matches!(err, AstarsError::UnsupportedEncoding(label) if label == "not-a-real-encoding"));
    }

    #[test]
    fn diagnostics_is_empty_for_valid_source() {
        let result = parse_str("x = 1\n", Lang::Python);
        assert!(result.tree.diagnostics().is_empty());
    }

    #[test]
    fn diagnostics_reports_syntax_errors() {
        let result = parse_str("def (:\n", Lang::Python);
        let diagnostics = result.tree.diagnostics();
        assert!(!diagnostics.is_empty());
        assert!(diagnostics.iter().all(|d| d.severity == Severity::Error));
    }
}

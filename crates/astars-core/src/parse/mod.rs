//! Internal `parse` package: parser-specific code lives here and only here.
//!
//! Nothing in this module is `pub` at the crate root - `mod parse;` in `lib.rs`
//! is a private module, so `ParseAdapter` is unreachable from outside the
//! crate regardless of its own visibility. This mirrors the
//! "parse «package, internal»" boundary in
//! `docs/architecture/syntax-tree-structure.drawio.svg`.

mod adapter;

pub(crate) use adapter::ParseAdapter;

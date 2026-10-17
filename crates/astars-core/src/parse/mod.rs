//! Internal `parse` package: parser-specific code lives here and only here.
//!
//! Nothing in this module is `pub` at the crate root - `mod parse;` in `lib.rs`
//! is a private module, so `ParseAdapter` / `RawTree` are unreachable from
//! outside the crate regardless of their own visibility. This mirrors the
//! "parse «package, internal»" boundary in
//! `docs/architecture/core-parse-spike.drawio.svg`.

mod adapter;
mod raw_tree;

pub(crate) use adapter::ParseAdapter;

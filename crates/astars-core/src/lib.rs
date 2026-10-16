//! Astars core engine: parse / normalize / map / query / edit.
//!
//! This crate is currently a placeholder skeleton for the Rust core migration.
//! See `docs/ACTION_ITEMS.ja.md` for the spike plan (tree-sitter + PyO3 + napi-rs)
//! and `docs/STRATEGY.ja.md` for the design bets this crate must honor:
//! binding-agnostic (no pyo3/napi-rs dependency here), parser-isolated.

pub fn placeholder() -> &'static str {
    "astars-core"
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn placeholder_works() {
        assert_eq!(placeholder(), "astars-core");
    }
}

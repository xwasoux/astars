//! PyO3 bindings for `astars-core`.
//!
//! Placeholder: this crate currently just proves the workspace wiring
//! (astars-py -> astars-core) builds and can call the real `parse_str` entry
//! point. Actual PyO3 glue (pyo3 + maturin) lands with the binding spike —
//! see `docs/ACTION_ITEMS.ja.md`.

pub fn placeholder() -> usize {
    astars_core::parse_str("def hello():\n    return 1\n", astars_core::Lang::Python).node_count
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn links_against_core() {
        assert!(placeholder() > 0);
    }
}

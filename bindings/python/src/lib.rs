//! PyO3 bindings for `astars-core`.
//!
//! Placeholder: this crate currently just re-exports a stub to prove the
//! workspace wiring (astars-py -> astars-core) builds. Actual PyO3 glue
//! (pyo3 + maturin) lands with the binding spike — see `docs/ACTION_ITEMS.ja.md`.

pub fn placeholder() -> &'static str {
    astars_core::placeholder()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn links_against_core() {
        assert_eq!(placeholder(), "astars-core");
    }
}

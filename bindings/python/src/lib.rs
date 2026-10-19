//! PyO3 bindings for `astars-core`.
//!
//! This crate is the only place allowed to depend on pyo3 - `astars-core`
//! itself stays binding-agnostic (see `docs/STRATEGY.ja.md`). `PyLang` and
//! `PyParseResult` exist purely to mirror `astars_core::Lang` /
//! `astars_core::ParseResult` across the FFI boundary; see
//! `docs/architecture/python-binding-spike.drawio.svg` for the class diagram
//! this module implements.
//!
//! Python side: `import _astars` (the eventual `import astars` is a separate,
//! pure-Python package that will wrap this native module - not built yet).

use pyo3::prelude::*;

/// Mirrors `astars_core::Lang`. Kept as a distinct type so `astars-core`
/// never has to depend on pyo3.
#[pyclass(eq, eq_int)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PyLang {
    Python,
}

impl From<PyLang> for astars_core::Lang {
    fn from(lang: PyLang) -> Self {
        match lang {
            PyLang::Python => astars_core::Lang::Python,
        }
    }
}

impl From<astars_core::Lang> for PyLang {
    fn from(lang: astars_core::Lang) -> Self {
        match lang {
            astars_core::Lang::Python => PyLang::Python,
        }
    }
}

/// Mirrors `astars_core::ParseResult`.
#[pyclass(get_all)]
#[derive(Debug, Clone, Copy)]
pub struct PyParseResult {
    pub lang: PyLang,
    pub node_count: usize,
}

impl From<astars_core::ParseResult> for PyParseResult {
    fn from(result: astars_core::ParseResult) -> Self {
        // node_count is a stand-in for exposing the full SyntaxTree across
        // the FFI boundary, which is its own design round (see
        // docs/architecture/syntax-tree-structure.drawio.svg's notes).
        let node_count = result.tree.walk().count();
        Self {
            lang: result.lang.into(),
            node_count,
        }
    }
}

#[pymethods]
impl PyParseResult {
    fn __repr__(&self) -> String {
        format!(
            "ParseResult(lang={:?}, node_count={})",
            self.lang, self.node_count
        )
    }
}

/// `_astars.parse_str(source, lang) -> ParseResult`: converts `PyLang` to
/// `astars_core::Lang`, calls `astars_core::parse_str`, converts the result
/// back to `PyParseResult`.
#[pyfunction]
fn parse_str(source: &str, lang: PyRef<'_, PyLang>) -> PyParseResult {
    astars_core::parse_str(source, (*lang).into()).into()
}

#[pymodule]
fn _astars(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLang>()?;
    m.add_class::<PyParseResult>()?;
    m.add_function(wrap_pyfunction!(parse_str, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn converts_lang_both_ways() {
        assert_eq!(astars_core::Lang::from(PyLang::Python), astars_core::Lang::Python);
        assert_eq!(PyLang::from(astars_core::Lang::Python), PyLang::Python);
    }

    #[test]
    fn parse_result_conversion_round_trips() {
        // Exercises the same conversion path parse_str() uses, without going
        // through PyRef extraction (which needs a live Python interpreter -
        // covered instead by the maturin/Python smoke test).
        let core_result = astars_core::parse_str("def hello():\n    return 1\n", astars_core::Lang::Python);
        let py_result: PyParseResult = core_result.into();
        assert_eq!(py_result.lang, PyLang::Python);
        assert!(py_result.node_count > 0);
    }
}

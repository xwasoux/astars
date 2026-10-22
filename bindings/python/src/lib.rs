//! PyO3 bindings for `astars-core`.
//!
//! This crate is the only place allowed to depend on pyo3 - `astars-core`
//! itself stays binding-agnostic (see `docs/STRATEGY.ja.md`). `PyLang`,
//! `PyParseResult`, `PySyntaxTree`, `PyNodeInfo`, `PyEditResult` and
//! `PyDiagnostic` exist purely to mirror `astars_core` types across the FFI
//! boundary; see the "bindings/python" class diagram in
//! `docs/architecture/ARCHITECTURE.ja.md` for the design this module
//! implements (the edit primitive and diagnostics behavior are explained in
//! `docs/architecture/EDIT_MODEL.ja.md` and `docs/SOURCE_MAPPING_PLAN.ja.md`).
//!
//! Python side: `import _astars` (the eventual `import astars` is a separate,
//! pure-Python package that will wrap this native module - not built yet).

use astars_core::NodeId;
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

/// One node's full detail, flattened out of `astars_core::SyntaxTree` for a
/// single FFI round trip. See `PySyntaxTree::node_info` (one node) vs
/// `PySyntaxTree::dump` (a whole subtree in one call).
#[pyclass(get_all)]
#[derive(Debug, Clone)]
pub struct PyNodeInfo {
    pub id: u32,
    pub kind: String,
    pub field_name: Option<String>,
    pub start_byte: usize,
    pub end_byte: usize,
    pub parent: Option<u32>,
    pub children: Vec<u32>,
}

impl PyNodeInfo {
    fn from_tree(tree: &astars_core::SyntaxTree, id: NodeId) -> Self {
        let span = tree.span_of(id);
        Self {
            id: id.as_u32(),
            kind: tree.kind_of(id).to_string(),
            field_name: tree.field_name_of(id).map(str::to_string),
            start_byte: span.start_byte,
            end_byte: span.end_byte,
            parent: tree.parent_of(id).map(NodeId::as_u32),
            children: tree.children_of(id).iter().map(|id| id.as_u32()).collect(),
        }
    }
}

/// Mirrors `astars_core::SyntaxTree`. A thin wrapper that converts `NodeId`
/// to/from plain `u32` at every method boundary - see the diagram's design
/// notes for why NodeId has no dedicated Python class.
#[pyclass]
pub struct PySyntaxTree {
    inner: astars_core::SyntaxTree,
}

impl From<astars_core::SyntaxTree> for PySyntaxTree {
    fn from(inner: astars_core::SyntaxTree) -> Self {
        Self { inner }
    }
}

#[pymethods]
impl PySyntaxTree {
    fn root_id(&self) -> u32 {
        self.inner.root().as_u32()
    }

    /// All node ids in preorder, collected into one `list[int]` - not a
    /// lazy iterator, so walking a large tree costs one FFI call, not one
    /// per node (EDIT_MODEL.ja.md operation 11).
    fn walk(&self) -> Vec<u32> {
        self.inner.walk().map(NodeId::as_u32).collect()
    }

    fn find(&self, kind: &str) -> Vec<u32> {
        self.inner.find(kind).into_iter().map(NodeId::as_u32).collect()
    }

    fn node_at(&self, offset: usize) -> Option<u32> {
        self.inner.node_at(offset).map(NodeId::as_u32)
    }

    fn span_of(&self, id: u32) -> (usize, usize) {
        let span = self.inner.span_of(NodeId::from_u32(id));
        (span.start_byte, span.end_byte)
    }

    fn source_of(&self, id: u32) -> String {
        self.inner.source_of(NodeId::from_u32(id))
    }

    /// One node's detail - a single, targeted FFI round trip.
    fn node_info(&self, id: u32) -> PyNodeInfo {
        PyNodeInfo::from_tree(&self.inner, NodeId::from_u32(id))
    }

    /// The whole subtree rooted at `id`, as one `list[PyNodeInfo]` - bulk
    /// export for rendering/serializing a tree without node-by-node FFI
    /// calls (EDIT_MODEL.ja.md scenario D / operation 11).
    fn dump(&self, id: u32) -> Vec<PyNodeInfo> {
        let mut result = Vec::new();
        let mut stack = vec![NodeId::from_u32(id)];
        while let Some(current) = stack.pop() {
            result.push(PyNodeInfo::from_tree(&self.inner, current));
            for &child in self.inner.children_of(current).iter().rev() {
                stack.push(child);
            }
        }
        result
    }

    fn __repr__(&self) -> String {
        format!("SyntaxTree(nodes={})", self.inner.walk().count())
    }

    /// Replace `target`'s source span with `new_text`, producing a new
    /// `PySyntaxTree` wrapped in a `PyEditResult`. `self` is untouched. See
    /// `docs/architecture/EDIT_MODEL.ja.md` ("編集 primitive(v1)の設計").
    fn replace(&self, target: u32, new_text: &str) -> PyEditResult {
        let edit = self.inner.replace(NodeId::from_u32(target), new_text);
        PyEditResult { inner: edit }
    }

    /// Did `id` (a node in `self`, the tree *before* some `edit`) survive
    /// into `edit.tree` unchanged? `id` must come from `self`, not from
    /// `edit.tree` - `NodeId`s from different trees are not comparable
    /// (see `docs/architecture/EDIT_MODEL.ja.md`).
    fn unchanged_in(&self, id: u32, edit: &PyEditResult) -> bool {
        self.inner.unchanged_in(NodeId::from_u32(id), &edit.inner)
    }

    /// Parser-recovery diagnostics for this tree (`ERROR` / `MISSING` nodes
    /// tree-sitter produced while parsing), in preorder. See
    /// `docs/SOURCE_MAPPING_PLAN.ja.md` ("Diagnostics Span").
    fn diagnostics(&self) -> Vec<PyDiagnostic> {
        self.inner.diagnostics().into_iter().map(PyDiagnostic::from_core).collect()
    }
}

/// Mirrors `astars_core::EditResult`. Holds the whole core `EditResult`
/// (not just its public `tree` field) because `changed_ranges` stays
/// private in `astars-core` - `PySyntaxTree::unchanged_in` needs the whole
/// thing, so this type cannot be decomposed down to just a tree handle.
#[pyclass]
pub struct PyEditResult {
    inner: astars_core::EditResult,
}

#[pymethods]
impl PyEditResult {
    /// The new tree. Clones `astars_core::SyntaxTree` (cheap-ish arena +
    /// source copy) because `&self` can't move `inner.tree` out while still
    /// needing `inner` intact afterward for `unchanged_in` calls.
    #[getter]
    fn tree(&self, py: Python<'_>) -> PyResult<Py<PySyntaxTree>> {
        Py::new(py, PySyntaxTree::from(self.inner.tree.clone()))
    }
}

/// Mirrors `astars_core::Diagnostic`. `severity` is flattened to a plain
/// string (`"error"`) since `astars_core::Severity` has a single variant in
/// v0 - not worth a dedicated Python enum yet.
#[pyclass(get_all)]
#[derive(Debug, Clone)]
pub struct PyDiagnostic {
    pub severity: String,
    pub message: String,
    pub span: (usize, usize),
}

impl PyDiagnostic {
    fn from_core(diagnostic: astars_core::Diagnostic) -> Self {
        Self {
            severity: match diagnostic.severity {
                astars_core::Severity::Error => "error".to_string(),
            },
            message: diagnostic.message,
            span: (diagnostic.span.start_byte, diagnostic.span.end_byte),
        }
    }
}

/// Mirrors `astars_core::ParseResult`.
#[pyclass(get_all)]
pub struct PyParseResult {
    pub lang: PyLang,
    pub tree: Py<PySyntaxTree>,
}

impl PyParseResult {
    fn from_core(py: Python<'_>, result: astars_core::ParseResult) -> PyResult<Self> {
        Ok(Self {
            lang: result.lang.into(),
            tree: Py::new(py, PySyntaxTree::from(result.tree))?,
        })
    }
}

#[pymethods]
impl PyParseResult {
    fn __repr__(&self) -> String {
        format!("ParseResult(lang={:?})", self.lang)
    }
}

/// `_astars.parse_str(source, lang) -> ParseResult`: converts `PyLang` to
/// `astars_core::Lang`, calls `astars_core::parse_str`, converts the result
/// back to `PyParseResult`.
#[pyfunction]
fn parse_str(py: Python<'_>, source: &str, lang: PyRef<'_, PyLang>) -> PyResult<PyParseResult> {
    let result = astars_core::parse_str(source, (*lang).into());
    PyParseResult::from_core(py, result)
}

/// `_astars.parse_bytes(source, lang) -> ParseResult`: like `parse_str`, but
/// `source` need not be valid UTF-8 (see `astars_core::parse_bytes`).
#[pyfunction]
fn parse_bytes(py: Python<'_>, source: &[u8], lang: PyRef<'_, PyLang>) -> PyResult<PyParseResult> {
    let result = astars_core::parse_bytes(source, (*lang).into());
    PyParseResult::from_core(py, result)
}

/// `_astars.parse_file(path, lang) -> ParseResult`: reads `path` and parses
/// it (see `astars_core::parse_file`). Raises `OSError` on an I/O failure.
#[pyfunction]
fn parse_file(py: Python<'_>, path: &str, lang: PyRef<'_, PyLang>) -> PyResult<PyParseResult> {
    let result = astars_core::parse_file(std::path::Path::new(path), (*lang).into())
        .map_err(|err| PyErr::new::<pyo3::exceptions::PyOSError, _>(err.to_string()))?;
    PyParseResult::from_core(py, result)
}

#[pymodule]
fn _astars(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLang>()?;
    m.add_class::<PyParseResult>()?;
    m.add_class::<PySyntaxTree>()?;
    m.add_class::<PyNodeInfo>()?;
    m.add_class::<PyEditResult>()?;
    m.add_class::<PyDiagnostic>()?;
    m.add_function(wrap_pyfunction!(parse_str, m)?)?;
    m.add_function(wrap_pyfunction!(parse_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(parse_file, m)?)?;
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
    fn node_id_round_trips_through_u32() {
        let tree = astars_core::parse_str("def hello():\n    return 1\n", astars_core::Lang::Python).tree;
        let root = tree.root();
        assert_eq!(NodeId::from_u32(root.as_u32()), root);
    }

    #[test]
    fn walk_and_node_info_agree_on_node_count() {
        let core_tree = astars_core::parse_str("def hello():\n    return 1\n", astars_core::Lang::Python).tree;
        let py_tree = PySyntaxTree::from(core_tree);
        let ids = py_tree.walk();
        assert!(!ids.is_empty());
        for id in &ids {
            // every walked id must resolve without panicking
            let _ = py_tree.node_info(*id);
        }
    }

    #[test]
    fn dump_returns_whole_subtree() {
        let core_tree = astars_core::parse_str("def hello():\n    return 1\n", astars_core::Lang::Python).tree;
        let py_tree = PySyntaxTree::from(core_tree);
        let root_id = py_tree.root_id();
        let dumped = py_tree.dump(root_id);
        assert_eq!(dumped.len(), py_tree.walk().len());
    }

    #[test]
    fn replace_and_unchanged_in_round_trip() {
        let core_tree = astars_core::parse_str("x = 1\ny = 2\n", astars_core::Lang::Python).tree;
        let py_tree = PySyntaxTree::from(core_tree);
        let assignments = py_tree.find("assignment");
        assert_eq!(assignments.len(), 2);
        let (first, second) = (assignments[0], assignments[1]);

        let edit = py_tree.replace(first, "x = 99");
        assert!(!py_tree.unchanged_in(first, &edit));
        assert!(py_tree.unchanged_in(second, &edit));
    }

    #[test]
    fn diagnostics_reports_syntax_errors() {
        let core_tree = astars_core::parse_str("def (:\n", astars_core::Lang::Python).tree;
        let py_tree = PySyntaxTree::from(core_tree);
        let diagnostics = py_tree.diagnostics();
        assert!(!diagnostics.is_empty());
        assert!(diagnostics.iter().all(|d| d.severity == "error"));
    }

    #[test]
    fn parse_bytes_mirrors_parse_str_node_count() {
        let from_bytes = PySyntaxTree::from(astars_core::parse_bytes(b"x = 1\n", astars_core::Lang::Python).tree);
        let from_str = PySyntaxTree::from(astars_core::parse_str("x = 1\n", astars_core::Lang::Python).tree);
        assert_eq!(from_bytes.walk().len(), from_str.walk().len());
    }
}

//! PyO3 bindings for `astars-core`.
//!
//! This crate is the only place allowed to depend on pyo3 - `astars-core`
//! itself stays binding-agnostic (see `docs/STRATEGY.ja.md`). `PyLang`,
//! `PyParseResult`, `PySyntaxTree` and `PyNodeInfo` exist purely to mirror
//! `astars_core` types across the FFI boundary; see
//! `docs/architecture/python-tree-binding.drawio.svg` for the class diagram
//! this module implements.
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
        self.inner.source_of(NodeId::from_u32(id)).to_string()
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

#[pymodule]
fn _astars(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyLang>()?;
    m.add_class::<PyParseResult>()?;
    m.add_class::<PySyntaxTree>()?;
    m.add_class::<PyNodeInfo>()?;
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
}

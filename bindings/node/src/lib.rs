//! napi-rs bindings for `astars-core`.
//!
//! This crate is the only place allowed to depend on napi-rs - `astars-core`
//! itself stays binding-agnostic (see `docs/STRATEGY.ja.md`). `JsLang`,
//! `JsSyntaxTree`, `JsNodeInfo`, `JsEditResult` and `JsDiagnostic` exist
//! purely to mirror `astars_core` types across the FFI boundary; see the
//! "bindings/node" class diagram in `docs/architecture/ARCHITECTURE.ja.md`
//! for the design this module implements (the edit primitive and
//! diagnostics behavior are explained in `docs/architecture/EDIT_MODEL.ja.md`
//! and `docs/SOURCE_MAPPING_PLAN.ja.md`).
//!
//! Node side: `import { parseStr, JsLang } from '@astars/native'` (the
//! eventual `astars` / `@astars/core` npm package is a separate, thin
//! wrapper that will sit on top of this native module - not built yet).

#[macro_use]
extern crate napi_derive;

use astars_core::NodeId;

/// Mirrors `astars_core::Lang`. Kept as a distinct type so `astars-core`
/// never has to depend on napi-rs.
#[napi]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum JsLang {
    Python,
}

impl From<JsLang> for astars_core::Lang {
    fn from(lang: JsLang) -> Self {
        match lang {
            JsLang::Python => astars_core::Lang::Python,
        }
    }
}

impl From<astars_core::Lang> for JsLang {
    fn from(lang: astars_core::Lang) -> Self {
        match lang {
            astars_core::Lang::Python => JsLang::Python,
        }
    }
}

/// One node's full detail, flattened out of `astars_core::SyntaxTree` for a
/// single FFI round trip. See `JsSyntaxTree::node_info` (one node) vs
/// `JsSyntaxTree::dump` (a whole subtree in one call).
#[napi(object)]
#[derive(Debug, Clone)]
pub struct JsNodeInfo {
    pub id: u32,
    pub kind: String,
    pub field_name: Option<String>,
    pub start_byte: u32,
    pub end_byte: u32,
    pub parent: Option<u32>,
    pub children: Vec<u32>,
}

impl JsNodeInfo {
    fn from_tree(tree: &astars_core::SyntaxTree, id: NodeId) -> Self {
        let span = tree.span_of(id);
        Self {
            id: id.as_u32(),
            kind: tree.kind_of(id).to_string(),
            field_name: tree.field_name_of(id).map(str::to_string),
            start_byte: span.start_byte as u32,
            end_byte: span.end_byte as u32,
            parent: tree.parent_of(id).map(NodeId::as_u32),
            children: tree.children_of(id).iter().map(|id| id.as_u32()).collect(),
        }
    }
}

/// Mirrors `astars_core::SyntaxTree` - and also carries `lang`, which in
/// `astars_core::ParseResult` lives one level up. Deviation from the
/// diagram: there is no separate `JsParseResult` class. napi-rs's
/// `#[napi(object)]` requires every field to implement `FromNapiValue`
/// (bidirectional JS<->Rust conversion), which a `#[napi]` class instance
/// does not - so a plain object cannot hold a `JsSyntaxTree` field, and a
/// `#[napi]` class getter cannot return a borrowed or freshly-constructed
/// class instance either without `Reference<T>` plumbing. Folding `lang`
/// into `JsSyntaxTree` itself sidesteps that entirely: `parseStr` returns
/// a `JsSyntaxTree` directly. (Python's `Py<PySyntaxTree>` inside
/// `PyParseResult` hit the same "class-in-object" problem but pyo3 has a
/// direct answer for it; napi-rs does not, as cleanly.)
#[napi]
pub struct JsSyntaxTree {
    inner: astars_core::SyntaxTree,
    lang: JsLang,
}

impl JsSyntaxTree {
    fn new(lang: JsLang, inner: astars_core::SyntaxTree) -> Self {
        Self { inner, lang }
    }
}

#[napi]
impl JsSyntaxTree {
    #[napi(getter)]
    pub fn lang(&self) -> JsLang {
        self.lang
    }

    #[napi]
    pub fn root_id(&self) -> u32 {
        self.inner.root().as_u32()
    }

    /// All node ids in preorder, collected into one `number[]` - not a
    /// lazy iterator, so walking a large tree costs one FFI call, not one
    /// per node (EDIT_MODEL.ja.md operation 11).
    #[napi]
    pub fn walk(&self) -> Vec<u32> {
        self.inner.walk().map(NodeId::as_u32).collect()
    }

    #[napi]
    pub fn find(&self, kind: String) -> Vec<u32> {
        self.inner.find(&kind).into_iter().map(NodeId::as_u32).collect()
    }

    #[napi]
    pub fn node_at(&self, offset: u32) -> Option<u32> {
        self.inner.node_at(offset as usize).map(NodeId::as_u32)
    }

    #[napi]
    pub fn span_of(&self, id: u32) -> Vec<u32> {
        let span = self.inner.span_of(NodeId::from_u32(id));
        vec![span.start_byte as u32, span.end_byte as u32]
    }

    #[napi]
    pub fn source_of(&self, id: u32) -> String {
        self.inner.source_of(NodeId::from_u32(id))
    }

    /// One node's detail - a single, targeted FFI round trip.
    #[napi]
    pub fn node_info(&self, id: u32) -> JsNodeInfo {
        JsNodeInfo::from_tree(&self.inner, NodeId::from_u32(id))
    }

    /// The whole subtree rooted at `id`, as one `JsNodeInfo[]` - bulk export
    /// for rendering/serializing a tree without node-by-node FFI calls
    /// (EDIT_MODEL.ja.md scenario D / operation 11).
    #[napi]
    pub fn dump(&self, id: u32) -> Vec<JsNodeInfo> {
        let mut result = Vec::new();
        let mut stack = vec![NodeId::from_u32(id)];
        while let Some(current) = stack.pop() {
            result.push(JsNodeInfo::from_tree(&self.inner, current));
            for &child in self.inner.children_of(current).iter().rev() {
                stack.push(child);
            }
        }
        result
    }

    /// Replace `target`'s source span with `new_text`, producing a new
    /// `JsSyntaxTree` wrapped in a `JsEditResult`. `self` is untouched. See
    /// `docs/architecture/EDIT_MODEL.ja.md` ("編集 primitive(v1)の設計").
    #[napi]
    pub fn replace(&self, target: u32, new_text: String) -> JsEditResult {
        let edit = self.inner.replace(NodeId::from_u32(target), &new_text);
        JsEditResult { inner: edit }
    }

    /// Did `id` (a node in `self`, the tree *before* some `edit`) survive
    /// into `edit.tree` unchanged? `id` must come from `self`, not from
    /// `edit.tree` - `NodeId`s from different trees are not comparable
    /// (see `docs/architecture/EDIT_MODEL.ja.md`).
    #[napi]
    pub fn unchanged_in(&self, id: u32, edit: &JsEditResult) -> bool {
        self.inner.unchanged_in(NodeId::from_u32(id), &edit.inner)
    }

    /// Parser-recovery diagnostics for this tree (`ERROR` / `MISSING` nodes
    /// tree-sitter produced while parsing), in preorder. See
    /// `docs/SOURCE_MAPPING_PLAN.ja.md` ("Diagnostics Span").
    #[napi]
    pub fn diagnostics(&self) -> Vec<JsDiagnostic> {
        self.inner.diagnostics().into_iter().map(JsDiagnostic::from_core).collect()
    }
}

/// Mirrors `astars_core::EditResult`. Holds the whole core `EditResult` (not
/// just its public `tree` field) because `changed_ranges` stays private in
/// `astars-core` - `JsSyntaxTree::unchanged_in` needs the whole thing, so
/// this type cannot be decomposed down to just a tree handle.
#[napi]
pub struct JsEditResult {
    inner: astars_core::EditResult,
}

#[napi]
impl JsEditResult {
    /// The new tree. Clones `astars_core::SyntaxTree` (cheap-ish arena +
    /// source copy) because `&self` can't move `inner.tree` out while still
    /// needing `inner` intact afterward for `unchanged_in` calls.
    #[napi(getter)]
    pub fn tree(&self) -> JsSyntaxTree {
        let cloned = self.inner.tree.clone();
        let lang = cloned.lang().into();
        JsSyntaxTree::new(lang, cloned)
    }
}

/// Mirrors `astars_core::Diagnostic`. `severity` is flattened to a plain
/// string (`"error"`) since `astars_core::Severity` has a single variant in
/// v0 - not worth a dedicated JS enum yet.
#[napi(object)]
#[derive(Debug, Clone)]
pub struct JsDiagnostic {
    pub severity: String,
    pub message: String,
    pub span: Vec<u32>,
}

impl JsDiagnostic {
    fn from_core(diagnostic: astars_core::Diagnostic) -> Self {
        Self {
            severity: match diagnostic.severity {
                astars_core::Severity::Error => "error".to_string(),
            },
            message: diagnostic.message,
            span: vec![diagnostic.span.start_byte as u32, diagnostic.span.end_byte as u32],
        }
    }
}

/// `parseStr(source, lang) -> JsSyntaxTree`: converts `JsLang` to
/// `astars_core::Lang`, calls `astars_core::parse_str`, converts the result
/// (`astars_core::ParseResult { lang, tree }`) into a `JsSyntaxTree` that
/// carries both.
#[napi]
pub fn parse_str(source: String, lang: JsLang) -> JsSyntaxTree {
    let result = astars_core::parse_str(&source, lang.into());
    JsSyntaxTree::new(result.lang.into(), result.tree)
}

/// `parseBytes(source, lang) -> JsSyntaxTree`: like `parseStr`, but `source`
/// (a Node `Buffer`) need not be valid UTF-8 (see `astars_core::parse_bytes`).
#[napi]
pub fn parse_bytes(source: napi::bindgen_prelude::Buffer, lang: JsLang) -> JsSyntaxTree {
    let result = astars_core::parse_bytes(&source, lang.into());
    JsSyntaxTree::new(result.lang.into(), result.tree)
}

/// `parseFile(path, lang) -> JsSyntaxTree`: reads `path` and parses it (see
/// `astars_core::parse_file`). Throws on an I/O failure.
#[napi]
pub fn parse_file(path: String, lang: JsLang) -> napi::Result<JsSyntaxTree> {
    let result = astars_core::parse_file(std::path::Path::new(&path), lang.into())
        .map_err(|err| napi::Error::from_reason(err.to_string()))?;
    Ok(JsSyntaxTree::new(result.lang.into(), result.tree))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn converts_lang_both_ways() {
        assert_eq!(astars_core::Lang::from(JsLang::Python), astars_core::Lang::Python);
        assert_eq!(JsLang::from(astars_core::Lang::Python), JsLang::Python);
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
        let js_tree = JsSyntaxTree::new(JsLang::Python, core_tree);
        let ids = js_tree.walk();
        assert!(!ids.is_empty());
        for id in &ids {
            let _ = js_tree.node_info(*id);
        }
    }

    #[test]
    fn dump_returns_whole_subtree() {
        let core_tree = astars_core::parse_str("def hello():\n    return 1\n", astars_core::Lang::Python).tree;
        let js_tree = JsSyntaxTree::new(JsLang::Python, core_tree);
        let root_id = js_tree.root_id();
        let dumped = js_tree.dump(root_id);
        assert_eq!(dumped.len(), js_tree.walk().len());
    }

    #[test]
    fn replace_and_unchanged_in_round_trip() {
        let core_tree = astars_core::parse_str("x = 1\ny = 2\n", astars_core::Lang::Python).tree;
        let js_tree = JsSyntaxTree::new(JsLang::Python, core_tree);
        let assignments = js_tree.find("assignment".to_string());
        assert_eq!(assignments.len(), 2);
        let (first, second) = (assignments[0], assignments[1]);

        let edit = js_tree.replace(first, "x = 99".to_string());
        assert!(!js_tree.unchanged_in(first, &edit));
        assert!(js_tree.unchanged_in(second, &edit));
    }

    #[test]
    fn diagnostics_reports_syntax_errors() {
        let core_tree = astars_core::parse_str("def (:\n", astars_core::Lang::Python).tree;
        let js_tree = JsSyntaxTree::new(JsLang::Python, core_tree);
        let diagnostics = js_tree.diagnostics();
        assert!(!diagnostics.is_empty());
        assert!(diagnostics.iter().all(|d| d.severity == "error"));
    }

    #[test]
    fn parse_bytes_mirrors_parse_str_node_count() {
        let from_bytes = JsSyntaxTree::new(
            JsLang::Python,
            astars_core::parse_bytes(b"x = 1\n", astars_core::Lang::Python).tree,
        );
        let from_str = JsSyntaxTree::new(JsLang::Python, astars_core::parse_str("x = 1\n", astars_core::Lang::Python).tree);
        assert_eq!(from_bytes.walk().len(), from_str.walk().len());
    }
}

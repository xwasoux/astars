//! napi-rs bindings for `astars-core`.
//!
//! This crate is the only place allowed to depend on napi-rs - `astars-core`
//! itself stays binding-agnostic (see `docs/STRATEGY.ja.md`). `JsLang` and
//! `JsParseResult` exist purely to mirror `astars_core::Lang` /
//! `astars_core::ParseResult` across the FFI boundary; see
//! `docs/architecture/node-binding-spike.drawio.svg` for the class diagram
//! this module implements.
//!
//! Node side: `import { parseStr, JsLang } from '@astars/native'` (the
//! eventual `astars` / `@astars/core` npm package is a separate, thin
//! wrapper that will sit on top of this native module - not built yet).

#[macro_use]
extern crate napi_derive;

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

/// Mirrors `astars_core::ParseResult`. A plain `#[napi(object)]` rather than
/// a `#[napi]` class: it carries no methods, so there is no reason to pay
/// for a full JS class instance (see the diagram's design notes).
#[napi(object)]
#[derive(Debug, Clone, Copy)]
pub struct JsParseResult {
    pub lang: JsLang,
    pub node_count: u32,
}

impl From<astars_core::ParseResult> for JsParseResult {
    fn from(result: astars_core::ParseResult) -> Self {
        // node_count is a stand-in for exposing the full SyntaxTree across
        // the FFI boundary, which is its own design round (see
        // docs/architecture/syntax-tree-structure.drawio.svg's notes).
        let node_count = result.tree.walk().count();
        Self {
            lang: result.lang.into(),
            // tree-sitter node counts fit comfortably in u32; napi has no
            // native usize, and JS numbers can't losslessly hold full usize
            // range anyway.
            node_count: node_count as u32,
        }
    }
}

/// `parseStr(source, lang) -> JsParseResult`: converts `JsLang` to
/// `astars_core::Lang`, calls `astars_core::parse_str`, converts the result
/// back to `JsParseResult`.
#[napi]
pub fn parse_str(source: String, lang: JsLang) -> JsParseResult {
    astars_core::parse_str(&source, lang.into()).into()
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
    fn parse_str_calls_through_to_core() {
        let result = parse_str("def hello():\n    return 1\n".to_string(), JsLang::Python);
        assert_eq!(result.lang, JsLang::Python);
        assert!(result.node_count > 0);
    }
}

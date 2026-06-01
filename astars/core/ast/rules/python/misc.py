from astars.core.ast.rules.base import Rule, ChildRule

# --------------------------------------------
# Python misc / structural rules
# --------------------------------------------
# Goal:
# - Give the AST a stable "skeleton" (Module, Block)
# - Make top-level and block statements appear in the tree
# - Keep ExpressionStatement as a semantic wrapper (or passthrough)
#
# Notes:
# - tree-sitter-python uses "module" as the root node type.
# - Indented suites are typically "block".
# - A bare expression at statement position becomes "expression_statement".
#

PY_MISC_RULES = [
    # Root node of a file
    Rule(
        cst="module",
        ast="Module",
        children=[
            ChildRule(name="body", source="children", many=True),
        ],
    ),

    # Indented suite: if/elif/else/for/while/try/with bodies
    Rule(
        cst="block",
        ast="Block",
        children=[
            ChildRule(name="statements", source="children", many=True),
        ],
    ),

    # Statement wrapper around an expression (e.g. `a`, `foo()`)
    # If you don't want it in AST, keep passthrough.
    Rule(
        cst="expression_statement",
        ast="ExpressionStatement",
        passthrough="children",
    ),

    # Type annotation: : Type
    # Used in typed parameters and variable annotations.
    Rule(
        cst="type",
        ast="Type",
        children=[
            ChildRule(name="name", source="children", literal=True),
        ],
    ),

    # ============================================================
    # import a / import a.b as c
    # ============================================================
    Rule(
        cst="import_statement",
        ast="ImportStatement",
        children=[
            # confirmed: only aliased_import via field:name
            ChildRule(name="imports", source="field:name", many=True),
        ],
    ),

    # ============================================================
    # from x import y / from . import z / from x import *
    # ============================================================
    Rule(
        cst="import_from_statement",
        ast="ImportFromStatement",
        children=[
            # confirmed: absolute module
            ChildRule(name="module", source="field:module_name"),
            # relative import (field 無し)
            ChildRule(name="module", source="type:relative_import"),

            # imported names
            ChildRule(name="names", source="type:aliased_import", many=True),
            ChildRule(name="names", source="type:wildcard_import"),
        ],
    ),

    # ============================================================
    # a.b as c
    # ============================================================
    Rule(
        cst="aliased_import",
        ast="AliasedImport",
        children=[
            ChildRule(name="name", source="field:name"),
            ChildRule(name="alias", source="field:alias"),
        ],
    ),

    # ============================================================
    # a.b.c
    # ============================================================
    Rule(
        cst="dotted_name",
        ast="DottedName",
        children=[
            ChildRule(name="parts", source="type:identifier", many=True),
        ],
    ),

    # ============================================================
    # from . import x / from ..a import y
    # ============================================================
    Rule(
        cst="relative_import",
        ast="RelativeImport",
        children=[
            # import_prefix ('.' / '..') + optional dotted_name
            ChildRule(name="parts", source="children", many=True),
        ],
    ),

    # ============================================================
    # from x import *
    # ============================================================
    Rule(
        cst="wildcard_import",
        ast="WildcardImport",
    ),


]

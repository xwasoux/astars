from astars.core.ast.rules.base import Rule, ChildRule

# --------------------------------------------
# Python class declaration rules
# --------------------------------------------
#
# tree-sitter-python (0.25.x typical):
# - class_definition:
#     field:name         -> identifier
#     field:superclasses -> argument_list (optional)
#     field:body         -> block
#
# superclasses is usually an argument_list, which is already handled
# by expr.py (ArgumentList).
#

PY_CLASS_RULES = [
    # ----------------------------
    # class Foo(...): <block>
    # ----------------------------
    Rule(
        cst="class_definition",
        ast="ClassDef",
        children=[
            ChildRule(name="name", source="field:name"),

            # base classes / mixins (optional)
            ChildRule(name="bases", source="field:superclasses"),

            # class body
            ChildRule(name="body", source="field:body"),
        ],
    ),
]

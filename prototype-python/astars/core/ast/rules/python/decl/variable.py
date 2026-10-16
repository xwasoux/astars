from astars.core.ast.rules.base import Rule, ChildRule

PY_VARIABLE_RULES = [
    # ----------------------------
    # a = expr
    # confirmed: left/right
    # ----------------------------
    Rule(
        cst="assignment",
        ast="Assignment",
        children=[
            ChildRule(name="target", source="field:left"),
            ChildRule(name="value", source="field:right"),
        ],
    ),

    # ----------------------------
    # a += expr, a -= expr, ...
    # confirmed: left/operator/right
    # operator is a tiny raw node with text like "+=" (expected)
    # ----------------------------
    Rule(
        cst="augmented_assignment",
        ast="AugmentedAssignment",
        children=[
            ChildRule(name="target", source="field:left"),
            ChildRule(name="operator", source="field:operator", literal=True),
            ChildRule(name="value", source="field:right"),
        ],
    ),

    # ----------------------------
    # named expression: (a := expr)
    # still unconfirmed (common: name/value OR left/right)
    # ----------------------------
    Rule(
        cst="named_expression",
        ast="NamedExpression",
        children=[
            ChildRule(name="target", source="field:name"),
            ChildRule(name="value", source="field:value"),
        ],
    ),
]

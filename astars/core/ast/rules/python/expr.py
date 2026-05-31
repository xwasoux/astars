from astars.core.ast.rules.base import Rule, ChildRule

PY_EXPR_RULES = [
    # ----------------------------
    # call: foo(x, y)
    # ----------------------------
    Rule(
        cst="call",
        ast="CallExpression",
        children=[
            ChildRule(name="function", source="field:function"),
            ChildRule(name="arguments", source="field:arguments"),
        ],
    ),

    Rule(
        cst="argument_list",
        ast="ArgumentList",
        children=[
            ChildRule(name="items", source="children", many=True),
        ],
    ),

    # ----------------------------
    # attribute: obj.attr
    # ----------------------------
    Rule(
        cst="attribute",
        ast="MemberExpression",
        children=[
            ChildRule(name="object", source="field:object"),
            ChildRule(name="member", source="field:attribute"),
        ],
    ),

    # ----------------------------
    # parenthesized: (expr)
    # ----------------------------
    Rule(
        cst="parenthesized_expression",
        ast="ParenExpression",
        children=[
            ChildRule(name="expression", source="children"),
        ],
    ),

    # ----------------------------
    # comparisons: a == b, a < b ...
    # ----------------------------
    Rule(
        cst="comparison_operator",
        ast="ComparisonExpression",
        children=[
            ChildRule(name="left", source="field:left"),
            ChildRule(name="right", source="field:right"),
        ],
    ),

    # ----------------------------
    # boolean ops: a and b, a or b
    # tree-sitter-python commonly uses boolean_operator
    # ----------------------------
    Rule(
        cst="boolean_operator",
        ast="BooleanExpression",
        children=[
            ChildRule(name="left", source="field:left"),
            ChildRule(name="right", source="field:right"),
        ],
    ),

    # ----------------------------
    # binary ops: a + b, a * b, a | b ...
    # node type naming can vary by grammar version.
    # We support both common variants by mapping both to BinaryExpression.
    # ----------------------------
    Rule(
        cst="binary_operator",
        ast="BinaryExpression",
        children=[
            ChildRule(name="left", source="field:left"),
            ChildRule(name="right", source="field:right"),
        ],
    ),
    Rule(
        cst="binary_expression",
        ast="BinaryExpression",
        children=[
            ChildRule(name="left", source="field:left"),
            ChildRule(name="right", source="field:right"),
        ],
    ),

    # ----------------------------
    # unary ops: -x, +x, ~x
    # not: not x (may be not_operator)
    # Again, type naming can vary.
    # ----------------------------
    Rule(
        cst="unary_operator",
        ast="UnaryExpression",
        children=[
            ChildRule(name="operand", source="field:argument"),
        ],
    ),
    Rule(
        cst="not_operator",
        ast="NotExpression",
        children=[
            ChildRule(name="operand", source="field:argument"),
        ],
    ),

    # ----------------------------
    # subscripts: a[b]
    # Useful very early (common in real code)
    # ----------------------------
    Rule(
        cst="subscript",
        ast="SubscriptExpression",
        children=[
            ChildRule(name="value", source="field:value"),
            ChildRule(name="index", source="field:subscript"),
        ],
    ),

    # ----------------------------
    # as-patterns: Exception as e
    # ----------------------------
    Rule(
        cst="as_pattern",
        ast="AsPattern",
        children=[
            # as_pattern は field が付かないことが多いので type で拾うのが堅い
            ChildRule(name="value", source="children"),          # 例外型（identifier や attribute）
            ChildRule(name="name", source="type:identifier"),    # "as e"
        ],
    ),

    # ----------------------------
    # await expression
    # ----------------------------
    Rule(
        cst="await",
        ast="AwaitExpression",
        children=[
            ChildRule(name="operand", source="type:call"),
            ChildRule(name="operand", source="type:identifier"),
            ChildRule(name="operand", source="type:attribute"),
            ChildRule(name="operand", source="type:subscript"),
            ChildRule(name="operand", source="type:parenthesized_expression"),
        ],
    ),

    Rule(
        cst="await_expression",
        ast="AwaitExpression",
        children=[
            ChildRule(name="operand", source="type:call"),
            ChildRule(name="operand", source="type:identifier"),
            ChildRule(name="operand", source="type:attribute"),
            ChildRule(name="operand", source="type:subscript"),
        ],
    ),

]

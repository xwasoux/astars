from astars.core.ast.rules.base import Rule, ChildRule

# Confirmed by dumps (tree-sitter-python 0.25.x):
# - if_statement: condition, consequence, alternative(elif_clause|else_clause)
# - elif_clause: condition, consequence
# - else_clause: body
# - while_statement: condition, body
# - for_statement: left, right, body

PY_CONTROL_RULES = [
    # ----------------------------
    # if / elif / else (NO flattening)
    # ----------------------------
    Rule(
        cst="if_statement",
        ast="IfStatement",
        children=[
            ChildRule(name="test", source="field:condition"),
            ChildRule(name="body", source="field:consequence"),
            ChildRule(name="elif_clauses", source="type:elif_clause", many=True),
            ChildRule(name="else_clause", source="type:else_clause"),
        ],
    ),

    Rule(
        cst="elif_clause",
        ast="ElifClause",
        children=[
            ChildRule(name="test", source="field:condition"),
            ChildRule(name="body", source="field:consequence"),
        ],
    ),

    Rule(
        cst="else_clause",
        ast="ElseClause",
        children=[
            ChildRule(name="body", source="field:body"),
        ],
    ),

    # ----------------------------
    # while
    # ----------------------------
    Rule(
        cst="while_statement",
        ast="WhileStatement",
        children=[
            ChildRule(name="test", source="field:condition"),
            ChildRule(name="body", source="field:body"),
        ],
    ),

    # ----------------------------
    # for
    # ----------------------------
    Rule(
        cst="for_statement",
        ast="ForStatement",
        children=[
            ChildRule(name="target", source="field:left"),
            ChildRule(name="iter", source="field:right"),
            ChildRule(name="body", source="field:body"),
        ],
    ),

    # ----------------------------
    # simple control statements
    # ----------------------------
    Rule(cst="break_statement", ast="BreakStatement"),
    Rule(cst="continue_statement", ast="ContinueStatement"),
    Rule(cst="pass_statement", ast="PassStatement"),

    Rule(
        cst="return_statement",
        ast="ReturnStatement",
        children=[
            ChildRule(name="value", source="field:expression"),
        ],
    ),

    # ----------------------------
    # try / except / else / finally  (confirmed by dumps)
    # ----------------------------
    Rule(
        cst="try_statement",
        ast="TryStatement",
        children=[
            ChildRule(name="body", source="field:body"),
            ChildRule(name="handlers", source="type:except_clause", many=True),
            ChildRule(name="else_clause", source="type:else_clause"),
            ChildRule(name="finally_clause", source="type:finally_clause"),
        ],
    ),

    Rule(
        cst="except_clause",
        ast="ExceptClause",
        children=[
            # confirmed: exception info comes as as_pattern
            ChildRule(name="value", source="field:value"),
            # confirmed: handler body is an unfielded block
            ChildRule(name="body", source="type:block"),
        ],
    ),

    Rule(
        cst="finally_clause",
        ast="FinallyClause",
        children=[
            # confirmed: unfielded block
            ChildRule(name="body", source="type:block"),
        ],
    ),

    # ----------------------------
    # with statement
    # ----------------------------
    Rule(
        cst="with_statement",
        ast="WithStatement",
        children=[
            # with_clause の中に with_item がいる
            ChildRule(name="items", source="type:with_clause"),
            ChildRule(name="body", source="field:body"),
        ],
    ),

    Rule(
        cst="with_clause",
        ast="WithClause",
        children=[
            ChildRule(name="items", source="type:with_item", many=True),
        ],
    ),

    Rule(
        cst="with_item",
        ast="WithItem",
        children=[
            # confirmed: value is as_pattern
            ChildRule(name="value", source="field:value"),
        ],
    ),

]

from astars.core.ast.rules.base import Rule, ChildRule

PY_FUNCTION_RULES = [
    Rule(
        cst="function_definition",
        ast="FunctionDef",
        children=[
            ChildRule(name="name", source="field:name"),
            ChildRule(name="parameters", source="field:parameters"),
            ChildRule(name="returns", source="field:return_type"),
            ChildRule(name="body", source="field:body"),
        ],
    ),

    Rule(
        cst="parameters",
        ast="Parameters",
        children=[
            ChildRule(name="items", source="children", many=True),
        ],
    ),

    # def foo(a)
    # (still unconfirmed in your dump; kept minimal)
    Rule(
        cst="parameter",
        ast="Parameter",
        children=[
            ChildRule(name="name", source="type:identifier"),
        ],
    ),

    # def foo(b=1)
    # confirmed: name/value
    Rule(
        cst="default_parameter",
        ast="DefaultParameter",
        children=[
            ChildRule(name="name", source="field:name"),
            ChildRule(name="value", source="field:value"),
        ],
    ),

    # def foo(a: int)
    # (unconfirmed; adjust after dump)
    Rule(
        cst="typed_parameter",
        ast="TypedParameter",
        children=[
            ChildRule(name="name", source="type:identifier"),
            ChildRule(name="annotation", source="field:type"),
        ],
    ),


    # def foo(a: int = 1)
    # (unconfirmed; adjust after dump)
    Rule(
        cst="typed_default_parameter",
        ast="TypedDefaultParameter",
        children=[
            ChildRule(name="name", source="type:identifier"),
            ChildRule(name="annotation", source="field:type"),
            ChildRule(name="value", source="field:value"),
        ],
    ),

    # *args
    # confirmed children: "*" + identifier (both field:None)
    Rule(
        cst="list_splat_pattern",
        ast="VarPositionalParameter",
        children=[
            ChildRule(name="name", source="type:identifier"),
        ],
    ),

    # **kwargs
    # confirmed children: "**" + identifier (both field:None)
    Rule(
        cst="dictionary_splat_pattern",
        ast="VarKeywordParameter",
        children=[
            ChildRule(name="name", source="type:identifier"),
        ],
    ),

]

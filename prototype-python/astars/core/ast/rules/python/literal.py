from astars.core.ast.rules.base import Rule, ChildRule

PY_LITERAL_RULES = [

    # --- identifier ---
    Rule(
        cst="identifier",
        ast="Identifier",
        children=[
            # identifier は token child を持つので literal で拾う
            ChildRule("name", "children", literal=True),
        ],
    ),

    # --- numbers ---
    Rule(
        cst="integer",
        ast="IntegerLiteral",
        children=[
            ChildRule("value", "children", literal=True),
        ],
    ),

    Rule(
        cst="float",
        ast="FloatLiteral",
        children=[
            ChildRule("value", "children", literal=True),
        ],
    ),

    # --- string ---
    Rule(
        cst="string",
        ast="StringLiteral",
        children=[
            ChildRule("value", "type:string_content", literal=True, many=True),
        ],
    ),

    # --- true/false/none ---
    Rule(cst="true", ast="TrueLiteral"),
    Rule(cst="false", ast="FalseLiteral"),
    Rule(cst="none", ast="NoneLiteral"),
]

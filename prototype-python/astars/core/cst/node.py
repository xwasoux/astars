from dataclasses import dataclass
import uuid
import anytree

class CSTNode(anytree.NodeMixin):
    """
    CSTNode represents a single node in a Concrete Syntax Tree (CST).

    Responsibility
    --------------
    CSTNode is a *pure structural node* whose responsibility is to represent
    the syntactic structure and source-code location of a grammar element.

    This class intentionally:
      - DOES represent syntactic type and source-code ranges
      - DOES participate in a tree structure via anytree.NodeMixin
      - DOES provide a stable, CST-internal unique identifier (uid)

      - DOES NOT perform tree traversal logic
      - DOES NOT store or interpret source text
      - DOES NOT contain semantic or meaning-level information
        (those belong to AST nodes or higher-level analysis layers)

    In other words:
        CSTNode describes *where* and *what* a syntactic element is,
        but not *what it means*.

    Design Notes
    ------------
    - Tree traversal, searching, and querying are delegated to the CST object
      or to anytree utilities.
    - Source text access is delegated to the CST (via SourceText),
      using byte ranges stored in this node.
    - Semantic interpretation, symbol resolution, and control-flow analysis
      must be implemented in separate layers (e.g. AST).

    Relation to anytree
    -------------------
    - The `name` attribute is used as the node identifier within anytree.
      It is intended for identification and visualization purposes only
      and is NOT required to be globally unique.
    - Structural relationships (parent / children) are managed by anytree.

    Relation to tree-sitter
    -----------------------
    - CSTNode stores a *minimal, explicit subset* of information originating
      from a tree-sitter Node. 
      https://tree-sitter.github.io/py-tree-sitter/classes/tree_sitter.Node.html#tree_sitter.Node.grammar_name
    - tree-sitter traversal APIs, text extraction, and dynamic behaviors
      are intentionally excluded to prevent tight coupling.

    Attributes
    ----------
    name : str
        Identifier used by anytree for node identification and visualization.
        Not required to be unique across the CST.

    type : str
        Grammar node type (e.g. "function_definition", "if_statement").

    start_byte : int
        Start position (inclusive) of this node in the source text, in bytes.

    end_byte : int
        End position (exclusive) of this node in the source text, in bytes.

    grammar_id : int
        Grammar-specific internal identifier originating from the parser
        (e.g. tree-sitter node id). This value is unstable across parses
        and must not be used as an external identifier.

    grammar_name : str
        Human-readable grammar or rule name associated with this node.

    uid : str
        Stable, CST-internal unique identifier used for cross-layer mapping
        (e.g. CST ⇄ AST) and internal referencing.

    parent : CSTNode | None
        Parent node in the CST. Managed by anytree.

    Notes
    -----
    CSTNode instances are intended to be immutable after construction.
    If source code is edited, a new CST (and new CSTNode instances)
    should be created instead of mutating existing nodes.
    """

    def __init__(self,
                 *,
                 name:str,
                 parent:'CSTNode | None',
                 grammar_id:int,
                 grammar_name:str,
                 byte_range:tuple[int, int],
                 start_byte:int,
                 end_byte:int,
                 type:str,
                 unstable_id:int,
                 stable_id:str,
                 ):

        super().__init__()

        # Attributes originating from anytree
        self.name = name                    #A name or any other object this node can reference to as identifier.
        self.parent = parent

        # Attributes originating from py-tree-sitter Node
        self.grammar_id = grammar_id
        self.grammar_name = grammar_name
        self.byte_range = byte_range
        self.start_byte = start_byte
        self.end_byte = end_byte
        self.type = type

        self.stable_id = stable_id          #Retains identity even when regenerated. For external publication, diff/visualization/caching purposes.
        self.unstable_id = unstable_id      #Unique at build time, high-speed, for internal use

    def __repr__(self):
        return f"{self.__class__.__name__}{self.name, self.type}"

    def get_id(self) -> str:
        return self.stable_id

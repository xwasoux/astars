from anytree import RenderTree

from .node import CSTNode

class CST:
    """
    CST represents a Concrete Syntax Tree for a single source file or input.

    Responsibility
    --------------
    The CST class is responsible for managing and exposing the *entire*
    concrete syntax tree structure.

    This class:
      - OWNS the root CSTNode of the tree
      - DEFINES the language context in which the CST was constructed
      - PROVIDES tree-level representations and operations

    This class intentionally:
      - DOES NOT store semantic or meaning-level information
      - DOES NOT perform parsing or tree construction
        (those responsibilities belong to CSTFactory)
      - DOES NOT embed parser-specific APIs (e.g. tree-sitter traversal)

    In short:
        CST represents *the whole syntactic structure*,
        while CSTNode represents *a single syntactic element*.

    Design Notes
    ------------
    - All traversal, querying, and visualization operations should be
      expressed in terms of the root node and delegated to anytree utilities.
    - Parser-specific details are intentionally isolated from this class
      to keep the CST representation stable and reusable.

    Relation to CSTNode
    -------------------
    - CST acts as the aggregate root for CSTNode instances.
    - CSTNode instances should not exist independently of a CST instance
      in normal usage.
    - Tree structure integrity (parent / children relationships)
      is guaranteed by anytree.

    Relation to Language
    --------------------
    - The `language` attribute identifies the grammar or programming language
      used to construct this CST.
    - Language-specific behaviors should be implemented in separate layers
      (e.g. AST, analyzers, or transformers), not in this class.

    String Representation
    ---------------------
    - The string representation of CST is intended for debugging and
      visualization purposes.
    - It uses anytree.RenderTree and displays the `type` attribute of each
      CSTNode.

    Attributes
    ----------
    root : CSTNode
        The root node of the concrete syntax tree.

    language : str
        Identifier of the language or grammar used to generate this CST.

    Notes
    -----
    CST instances are intended to be immutable.
    If the source text changes, a new CST instance should be created
    rather than mutating an existing one.
    """

    def __init__(self, root:CSTNode, lang:str) -> None:
        self.root = root
        self.language = lang

    def __str__(self) -> str:
        return RenderTree(self.root).by_attr("type")

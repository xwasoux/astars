import tree_sitter

from .node import CSTNode
from .cst import CST

class CSTFactory:
    """
    Factory responsible for converting a parser-specific syntax tree
    (e.g. tree-sitter) into a Concrete Syntax Tree (CST).

    This class isolates all parser-dependent logic from the CST data model.
    """

    @staticmethod
    def createCST(tstree:tree_sitter.Node, lang:str) -> CST:
        """
            Create a CST from a tree-sitter parse tree.

            Parameters
            ----------
            tstree : tree_sitter.Tree
                Parse tree produced by tree-sitter.
            lang : str
                Language identifier used for parsing.

            Returns
            -------
            CST
                Constructed Concrete Syntax Tree.
            """
        tstree_root = tstree.root_node
        cst_root = _tstree2anytree(tstree_root, parent=None)
        return CST(root=cst_root, lang=lang)

def _addNode(tsnode:tree_sitter.Node, parent=None) -> CSTNode:
    return CSTNode(
        name=f"{tsnode.type}@{tsnode.start_byte}",
        parent=parent,
        grammar_id=tsnode.id,
        grammar_name=tsnode.type,
        start_byte=tsnode.start_byte,
        end_byte=tsnode.end_byte,
        byte_range=tsnode.end_byte - tsnode.start_byte,
        type=tsnode.type,
    )

def _tstree2anytree(tsnode:tree_sitter.Node, parent:CSTNode=None) -> CSTNode:
    """
    Recursively convert a tree-sitter Node into a CSTNode.
    """

    if parent == None:
        target = _addNode(tsnode=tsnode)
    else:
        target = _addNode(tsnode=tsnode, parent=parent)

    for child in tsnode.children:
        _tstree2anytree(child, target)

    return target

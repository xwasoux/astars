import tree_sitter

from .node import CSTNode
from .cst import CST

allAttr = [
    "child_by_field_id", "child_by_field_name", "child_count", 
    "children", "children_by_field_id", "children_by_field_name", 
    "end_byte", "end_point", "field_name_for_child", 
    "has_changes", "has_error", "id", 
    "is_missing", "is_named", "named_children_count", 
    "named_children", "next_named_sibling", "next_sibling",
    "parent", "prev_named_sibling", "prev_sibling", 
    "sexp", "start_byte", "start_point", 
    "text", "type", "walk"
    ]

tempAttr = [
    "child_by_field_id", "child_by_field_name", 
    "children_by_field_id", "end_byte", "end_point",
    "has_changes", "has_error", "id", 
    "is_missing", "is_named", 
    "sexp", "start_byte", "start_point", 
    "text", "type", "walk"
    ]

class CSTFactory:
    @staticmethod
    def createCST(tstree:tree_sitter.Node, code:str, lang:str) -> CST:
        tstree_root = tstree.root_node
        cst_root = _tstree2anytree(tstree_root)
        return CST(root=cst_root, code=code, lang=lang)

def _addNode(source, parent=None):
    sourceAttrs = dir(source)
    filterdAttrs = [attr for attr in sourceAttrs if attr in tempAttr]
    dictAttrs = {attr:getattr(source, attr) for attr in filterdAttrs}

    return CSTNode(name=str(dictAttrs["id"]), parent=parent, dictAttrs=dictAttrs)

def _tstree2anytree(source, parent:tree_sitter.Node=None) -> None:
    if parent == None:
        target = _addNode(source=source)
    else:
        target = _addNode(source=source, parent=parent)

    for child in source.children:
        _tstree2anytree(child, target)

    return target
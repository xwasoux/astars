from anytree import RenderTree
from anytree import find, find_by_attr, findall, findall_by_attr

from .node import CSTNode
from ..text import SourceText

class CST:
    def __init__(self, root:CSTNode, code:str, lang:str) -> None:
        self.root = root
        self.language = lang
        self.text = SourceText(code)
        self.is_edited = False

    def __str__(self) -> str:
        return RenderTree(self.root).by_attr("type")

    def searchNodeByID(self, id:str) -> tuple:
        return find_by_attr(node=self.root, value=id)

    def searchNodeByType(self, type:str) -> tuple:
        return findall_by_attr(node=self.root, value=type, name="type")

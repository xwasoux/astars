import os
import shutil
from typing import Any, Dict, List, Optional, Tuple, Union
from git import Repo
from tree_sitter import Language, Parser, Node

from ..nodes.node import ANode
from ._nodeAdd import _addNode
from ..tree import AParseTree
from ._utils import remove_comments_and_docstrings

class AParser:

    def __init__(self, lang: str) -> None:
        self.lang = lang

        if self.lang == "python":
            import tree_sitter_python as tspython
            self.ANY_LANGUAGE = Language(tspython.language())
        elif self.lang == "java":
            import tree_sitter_java as tsjava
            self.ANY_LANGUAGE = Language(tsjava.language())
        
    def preprocess(self, text: str) -> str:
        return remove_comments_and_docstrings(text, self.lang)

    def parse(self, text: str) -> None:
        parser = Parser(self.ANY_LANGUAGE)

        tree = parser.parse(bytes(text, "utf8"))
        cst = _ts2Anytree(source=tree.root_node, parent=None)

        parsetree = AParseTree(tree=cst, code=text, lang=self.lang)

        return parsetree

def _ts2Anytree(source, parent:ANode=None) -> None:
    if parent == None:
        target = _addNode(source=source)
    else:
        target = _addNode(source=source, parent=parent)

    for child in source.children:
        _ts2Anytree(child, target)

    return target

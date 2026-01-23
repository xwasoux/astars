import os
import shutil
from typing import Any, Dict, List, Optional, Tuple, Union
from tree_sitter import Language, Parser, Node

from ..cst.node import CSTNode
from ..cst import CST
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

        tstree = parser.parse(bytes(text, "utf8"))
        cst = CST(tstree=tstree.root_node, code=text, lang=self.lang)

        return cst

from .adapter import TreeSitterAdapter
from .builder import CSTBuilder


class CSTFactory:
    """
    Facade for building CST from parser-specific trees.
    """

    @staticmethod
    def from_tree_sitter(tstree, lang: str):
        raw = TreeSitterAdapter.to_raw(tstree)
        return CSTBuilder.build(raw, lang)

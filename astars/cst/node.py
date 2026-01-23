import anytree

class CSTNode(anytree.NodeMixin):
    allAttr = (
        "child_by_field_id", "child_by_field_name", "child_count", 
        "children", "children_by_field_id", "children_by_field_name", 
        "end_byte", "end_point", "field_name_for_child", 
        "has_changes", "has_error", "id", 
        "is_missing", "is_named", "named_children_count", 
        "named_children", "next_named_sibling", "next_sibling",
        "parent", "prev_named_sibling", "prev_sibling", 
        "sexp", "start_byte", "start_point", 
        "text", "type", "walk"
        )

    def __init__(self, name:str, parent=None, dictAttrs:dict=None, **kwargs):
        super().__init__()
        self.name = name
        self.parent = parent

        for key, val in dictAttrs.items():
            setattr(self, key, val)

        self.__dict__.update(kwargs)

    def __repr__(self):
        return f"{self.__class__.__name__}{self.name, self.type}"

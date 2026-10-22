from dataclasses import dataclass
from typing import List, Optional

@dataclass(frozen=True)
class RawChild:
    field_name: Optional[str]      # role of this child in parent grammar
    node: "RawSyntaxNode"


@dataclass(frozen=True)
class RawSyntaxNode:
    children: List[RawChild]
    origin_id: int

    grammar_id: int
    grammar_name: str

    start_byte: int
    start_point: tuple[int, int]
    end_byte: int
    end_point: tuple[int, int]

    is_named: bool
    is_missing: bool
    is_error: bool
    is_extra: bool
    is_async: bool

    kind_id: int
    type: str
    text: Optional[str]            # keep only for leaves if you want


    @property
    def byte_range(self) -> tuple[int,int]:
        return (self.start_byte, self.end_byte)


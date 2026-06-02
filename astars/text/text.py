from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, init=False)
class SourceText:
    source_code: str
    source_bytes: bytes

    def __init__(self, source_code: str = "", source_bytes: bytes | None = None):
        if not isinstance(source_code, str):
            raise TypeError(f"source_code must be str: {source_code!r}")
        if source_bytes is None:
            source_bytes = source_code.encode("utf-8")
        if not isinstance(source_bytes, bytes):
            raise TypeError(f"source_bytes must be bytes: {source_bytes!r}")

        object.__setattr__(self, "source_code", source_code)
        object.__setattr__(self, "source_bytes", source_bytes)

    @property
    def text(self) -> str:
        return self.source_code

    @property
    def length(self) -> int:
        return len(self.source_bytes)

    def validate_offset(self, byte_offset: int) -> None:
        if not isinstance(byte_offset, int) or isinstance(byte_offset, bool):
            raise ValueError(f"byte offset must be int: {byte_offset!r}")
        if byte_offset < 0 or byte_offset > self.length:
            raise ValueError(
                f"byte offset out of range: {byte_offset} "
                f"(source length: {self.length})"
            )

    def validate_range(self, start_byte: int, end_byte: int) -> None:
        self.validate_offset(start_byte)
        self.validate_offset(end_byte)
        if start_byte > end_byte:
            raise ValueError(
                f"byte range start must be <= end: {start_byte} > {end_byte}"
            )

    def is_eof(self, byte_offset: int) -> bool:
        self.validate_offset(byte_offset)
        return byte_offset == self.length

    def point_at(self, byte_offset: int) -> tuple[int, int]:
        self.validate_offset(byte_offset)

        line = 0
        line_start = 0
        for idx, byte in enumerate(self.source_bytes[:byte_offset]):
            if byte == 0x0A:
                line += 1
                line_start = idx + 1

        return (line, byte_offset - line_start)

    def slice_bytes(self, start_byte: int, end_byte: int) -> bytes:
        self.validate_range(start_byte, end_byte)
        return self.source_bytes[start_byte:end_byte]

    def slice_text(self, start_byte: int, end_byte: int) -> str:
        return self.slice_bytes(start_byte, end_byte).decode(
            "utf-8",
            errors="replace",
        )

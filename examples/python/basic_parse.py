"""Astars Rust core - usage example (Python binding).

Prerequisites (one-time build step, from bindings/python/):
    python3 -m venv .venv && source .venv/bin/activate
    pip install maturin
    maturin develop

Then run this file with that same venv active:
    python3 examples/python/basic_parse.py
"""

import os
import tempfile

import _astars

SOURCE = """\
def greet(name):
    return f"Hello, {name}!"


class Greeter:
    def __init__(self, name):
        self.name = name
"""


def main():
    tree = _astars.parse_str(SOURCE, _astars.PyLang.Python).tree
    print(f"parsed {len(tree.walk())} nodes")

    print("\nfunctions:")
    for node_id in tree.find("function_definition"):
        start, end = tree.span_of(node_id)
        print(f"  [{start}:{end}] {tree.source_of(node_id)!r}")

    print("\nclasses:")
    for node_id in tree.find("class_definition"):
        info = tree.node_info(node_id)
        print(f"  {info.kind} spans bytes {info.start_byte}-{info.end_byte}, "
              f"{len(info.children)} direct children")

    offset = SOURCE.index("Greeter")
    hit = tree.node_at(offset)
    print(f"\nnode at offset {offset} (inside 'Greeter'): {tree.node_info(hit).kind}")

    first_func = tree.find("function_definition")[0]
    subtree = tree.dump(first_func)
    print(f"\ndump() of the first function: {len(subtree)} nodes in one call")

    print("\npoint_at (0-based line/column for a byte offset):")
    line, column = tree.point_at(offset)
    print(f"  offset {offset} ('Greeter') is at line {line}, column {column}")

    print("\nedit primitive (replace + unchanged_in):")
    edit = tree.replace(first_func, 'def greet(name):\n    return f"Hi, {name}!"\n')
    class_def = tree.find("class_definition")[0]
    print(f"  replaced greet() - new tree has {len(edit.tree.walk())} nodes")
    print(f"  unchanged_in(class Greeter): {tree.unchanged_in(class_def, edit)}")
    print(f"  unchanged_in(greet, the node we replaced): {tree.unchanged_in(first_func, edit)}")

    print("\nparse_bytes (same source as raw bytes, not a str):")
    bytes_tree = _astars.parse_bytes(SOURCE.encode("utf-8"), _astars.PyLang.Python).tree
    print(f"  parsed {len(bytes_tree.walk())} nodes (matches parse_str: "
          f"{len(bytes_tree.walk()) == len(tree.walk())})")

    print("\nparse_file (writing SOURCE to a temp file first):")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(SOURCE)
        path = f.name
    try:
        file_tree = _astars.parse_file(path, _astars.PyLang.Python).tree
        print(f"  parsed {len(file_tree.walk())} nodes from {path}")
    finally:
        os.remove(path)

    print("\ndiagnostics (parsing a source with a syntax error):")
    broken = _astars.parse_str("def broken(:\n    pass\n", _astars.PyLang.Python).tree
    for diag in broken.diagnostics():
        print(f"  [{diag.severity}] {diag.message} at bytes {diag.span}")


if __name__ == "__main__":
    main()

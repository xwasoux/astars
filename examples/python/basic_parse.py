"""Astars Rust core - minimal usage example (Python binding).

Prerequisites (one-time build step, from bindings/python/):
    python3 -m venv .venv && source .venv/bin/activate
    pip install maturin
    maturin develop

Then run this file with that same venv active:
    python3 examples/python/basic_parse.py
"""

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


if __name__ == "__main__":
    main()

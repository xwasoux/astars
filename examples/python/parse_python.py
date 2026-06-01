from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import astars


def main():
    path = Path(__file__).resolve().parent / "input" / "python_sample.py"
    unit = astars.parse_file(path, lang="python")

    print(f"language: {unit.lang}")
    print(f"path: {unit.path}")
    print(f"root: {unit.root.kind}")
    print(f"diagnostics: {len(unit.diagnostics)}")

    functions = unit.find(kind="FunctionDef")
    print(f"functions: {len(functions)}")

    for function in functions[:3]:
        span = unit.span_of(function)
        source = unit.source_of(function)
        first_line = source.splitlines()[0] if source is not None else function.kind

        print()
        print(f"- {first_line}")
        print(f"  span: {span}")
        if source is not None:
            print("  source:")
            for line in source.splitlines()[:4]:
                print(f"    {line}")

    node = unit.node_at(4)
    print()
    print(f"node_at(4): {node.kind if node is not None else None}")


if __name__ == "__main__":
    main()

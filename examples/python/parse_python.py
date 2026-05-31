import os
from astars import AParser

def main():
    with open(os.path.join(os.path.dirname(__file__), "input", "python_sample.py")) as f:
        code = f.read()

    py_parser = AParser(lang="python")
    # code = py_parser.preprocess(text=code)
    cst = py_parser.parse(text=code)
    print(cst)

    return None


if __name__ == "__main__":
    main()
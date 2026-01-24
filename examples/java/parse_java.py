import os
from astars import AParser

def main():
    with open(os.path.join(os.path.dirname(__file__), "input", "java_sample.java")) as f:
        code = f.read()

    java_parser = AParser(lang="java")
    # code = java_parser.preprocess(text=code)
    cst = java_parser.parse(text=code)
    print(cst)

    return None


if __name__ == "__main__":
    main()
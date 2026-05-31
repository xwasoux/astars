from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import astars


SOURCE = "def hello(name):\n    return name\n"
UNICODE_SOURCE = 'def hello():\n    return "é"\n'


class PublicApiTests(unittest.TestCase):
    def test_parse_str_returns_source_unit(self):
        unit = astars.parse_str(SOURCE, lang="python")

        self.assertIsInstance(unit, astars.SourceUnit)
        self.assertEqual(unit.lang, "python")
        self.assertEqual(unit.source, SOURCE)
        self.assertEqual(unit.root.kind, "Module")
        self.assertEqual(unit.diagnostics, ())

    def test_find_span_source_and_node_at(self):
        unit = astars.parse_str(SOURCE, lang="python")

        functions = unit.find(kind="FunctionDef")
        self.assertEqual(len(functions), 1)

        function = functions[0]
        span = unit.span_of(function)

        self.assertEqual(span, astars.SourceSpan(0, 32, (0, 0), (1, 15)))
        self.assertEqual(unit.source_of(function), SOURCE.rstrip("\n"))
        self.assertEqual(unit.node_at(4).kind, "Identifier")

    def test_parse_bytes(self):
        unit = astars.parse_bytes(SOURCE.encode("utf-8"), lang="python")

        self.assertEqual(unit.source, SOURCE)
        self.assertEqual(unit.find(kind="FunctionDef")[0].kind, "FunctionDef")

    def test_parse_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.py"
            path.write_text(SOURCE, encoding="utf-8")

            unit = astars.parse_file(path, lang="python")

        self.assertEqual(unit.path, path)
        self.assertEqual(unit.source, SOURCE)
        self.assertEqual(unit.find(kind="FunctionDef")[0].kind, "FunctionDef")

    def test_unicode_source_uses_utf8_byte_offsets(self):
        unit = astars.parse_str(UNICODE_SOURCE, lang="python")

        function = unit.find(kind="FunctionDef")[0]
        expected_end = len(UNICODE_SOURCE.rstrip("\n").encode("utf-8"))

        self.assertEqual(
            unit.span_of(function),
            astars.SourceSpan(0, expected_end, (0, 0), (1, 15)),
        )
        self.assertEqual(unit.source_of(function), UNICODE_SOURCE.rstrip("\n"))

    def test_parse_file_respects_encoding(self):
        source = 'def hello():\n    return "あ"\n'

        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.py"
            path.write_bytes(source.encode("cp932"))

            unit = astars.parse_file(path, lang="python", encoding="cp932")

        function = unit.find(kind="FunctionDef")[0]
        expected_end = len(source.rstrip("\n").encode("utf-8"))

        self.assertEqual(unit.source, source)
        self.assertEqual(unit.source_of(function), source.rstrip("\n"))
        self.assertEqual(unit.span_of(function).end_byte, expected_end)

    def test_unsupported_language(self):
        with self.assertRaises(astars.UnsupportedLanguageError):
            astars.parse_str(SOURCE, lang="ruby")


if __name__ == "__main__":
    unittest.main()

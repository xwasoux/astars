from __future__ import annotations

import unittest

from astars.text import SourceText


class SourceTextTests(unittest.TestCase):
    def test_defaults_to_utf8_encoded_source_code(self):
        source = SourceText("\u00e9\nx")

        self.assertEqual(source.text, "\u00e9\nx")
        self.assertEqual(source.source_bytes, b"\xc3\xa9\nx")
        self.assertEqual(source.length, 4)
        self.assertEqual(source.point_at(0), (0, 0))
        self.assertEqual(source.point_at(2), (0, 2))
        self.assertEqual(source.point_at(3), (1, 0))
        self.assertEqual(source.point_at(4), (1, 1))

    def test_rejects_invalid_offsets_and_ranges(self):
        source = SourceText("abc")

        with self.assertRaises(ValueError):
            source.validate_offset(-1)

        with self.assertRaises(ValueError):
            source.validate_offset(4)

        with self.assertRaises(ValueError):
            source.validate_range(2, 1)

    def test_slices_by_byte_range(self):
        source = SourceText('return "\u00e9"')

        self.assertEqual(source.slice_bytes(8, 10), b"\xc3\xa9")
        self.assertEqual(source.slice_text(8, 10), "\u00e9")


if __name__ == "__main__":
    unittest.main()

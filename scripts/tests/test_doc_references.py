"""Reference discovery must avoid misleading issue-number and regex matches."""

import unittest

from scripts.doc_references import pattern


class References(unittest.TestCase):
    def test_issue_boundaries(self):
        matcher = pattern(119, ["placement"])
        for text in ("VIN-119", "#119.", "/issues/119", "PLACEMENT"):
            self.assertIsNotNone(matcher.search(text))
        for text in ("VIN-1190", "#1190", "/issues/1190"):
            self.assertIsNone(matcher.search(text))

    def test_feature_terms_are_literal(self):
        matcher = pattern(182, ["price.*", "C++"])
        self.assertIsNotNone(matcher.search("price.*"))
        self.assertIsNotNone(matcher.search("C++"))
        self.assertIsNone(matcher.search("price changed"))

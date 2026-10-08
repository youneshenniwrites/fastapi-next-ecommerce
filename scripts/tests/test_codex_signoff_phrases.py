"""Observed signoffs must satisfy VIN-325's grammar and match the reviewed head."""

import unittest
from pathlib import Path

from scripts.codex_review_gate import clean_result

FIXTURE = Path(__file__).with_name("fixtures") / "codex-signoff-phrases.txt"
REJECTED_OBSERVED = {":+1:", "Already looking forward to the next diff."}


def load_phrases(path=FIXTURE):
    """Return (source, phrase) pairs. Source comments sit directly above phrases."""
    entries = []
    source = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# source: copied "):
            source = "copied"
        elif line.startswith("# source: style"):
            source = "style"
        elif line.startswith("#") or not line.strip():
            continue
        else:
            if source is None:
                raise AssertionError(f"phrase lacks a source comment: {line}")
            entries.append((source, line))
            source = None
    return entries


class ExtraSignoffPhrases(unittest.TestCase):
    def test_every_fixture_phrase_obeys_parser_and_head_rules(self):
        """Accept valid fixtures only on their head; reject out-of-scope closings."""
        entries = load_phrases()
        phrases = [phrase for _, phrase in entries]
        self.assertEqual(len(entries), 52)
        self.assertEqual(len(phrases), len(set(phrases)))
        self.assertEqual(sum(source == "copied" for source, _ in entries), 9)
        self.assertEqual(sum(source == "style" for source, _ in entries), 43)
        sha = "c" * 40
        other = "d" * 40
        for source, phrase in entries:
            body = (
                "Codex Review: Didn't find any major issues. "
                f"{phrase}\n\n**Reviewed commit:** `{sha[:10]}`"
            )
            with self.subTest(phrase=phrase):
                if phrase not in REJECTED_OBSERVED:
                    self.assertLessEqual(len(phrase), 40)
                if source == "style":
                    self.assertLess(len(phrase), 40)
                    self.assertLessEqual(len(phrase.split()), 4)
                    self.assertTrue(phrase.endswith(("!", ".")))
                self.assertEqual(clean_result(body, sha), phrase not in REJECTED_OBSERVED)
                self.assertFalse(clean_result(body, other))

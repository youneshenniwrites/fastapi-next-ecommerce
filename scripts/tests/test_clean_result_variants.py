"""Observed bot wording must work without accepting arbitrary approval prose."""

import unittest

from scripts.codex_review_gate import CLEAN_RESULT_FOOTER, clean_result


class CleanVariants(unittest.TestCase):
    def test_observed_variants_with_and_without_footer(self):
        for signoff in ("Keep it up!", "Hooray!", "Keep them coming!"):
            result = f"Codex Review: Didn't find any major issues. {signoff}\n\n**Reviewed commit:** `aaaaaaaaaa`"
            for suffix in ("", CLEAN_RESULT_FOOTER):
                with self.subTest(signoff=signoff, footer=bool(suffix)):
                    self.assertTrue(clean_result(result + suffix, "a" * 40))
                    self.assertFalse(clean_result(result + suffix, "b" * 40))
                    self.assertFalse(
                        clean_result(
                            result + " Blocking issue found." + suffix, "a" * 40
                        )
                    )

    def test_unknown_signoff_stays_pending(self):
        self.assertFalse(
            clean_result(
                "Codex Review: Didn't find any major issues. Except a blocker! **Reviewed commit:** `aaaaaaaaaa`",
                "a" * 40,
            )
        )

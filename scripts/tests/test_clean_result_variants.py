"""A clean result is one short signoff, not a fixed list of phrases."""

import unittest

from scripts.codex_review_gate import CLEAN_RESULT_FOOTER, clean_result

PASSING = (
    "Can't wait for the next one!",
    "Swish!",
    "Keep it up!",
    "Hooray!",
    "Keep them coming!",
    "Delightful!",
    "You're on a roll.",
    ":rocket:",
    "Breezy!",
    "Everything looks fine!",
    "Swish?",
    "prefix!",
)

REJECTED = (
    "Except a blocker!",
    "Swish! But there are issues.",
    "Delightful! But fix this.",
    "You're on a roll. But fix this.",
    ":rocket: But fix this.",
    ":rocket",
    "🚀",
    "",
    "Nice job. Thanks!",
    "fix!",
    "A" * 41,
)


class CleanVariants(unittest.TestCase):
    def comment(self, signoff, sha="a" * 40, trailer=""):
        return (
            f"Codex Review: Didn't find any major issues. {signoff}\n\n"
            f"**Reviewed commit:** `{sha[:10]}`{trailer}"
        )

    def test_short_signoffs_pass_with_and_without_footer(self):
        self.assertLessEqual(len("Can't wait for the next one!"), 40)
        self.assertEqual(len("A" * 40), 40)
        self.assertTrue(clean_result(self.comment("A" * 40), "a" * 40))
        for signoff in PASSING:
            for trailer in ("", CLEAN_RESULT_FOOTER):
                with self.subTest(signoff=signoff, footer=bool(trailer)):
                    self.assertTrue(
                        clean_result(self.comment(signoff, trailer=trailer), "a" * 40)
                    )
                    self.assertFalse(
                        clean_result(self.comment(signoff, trailer=trailer), "b" * 40)
                    )

    def test_rejected_signoffs_stay_pending(self):
        for signoff in REJECTED:
            with self.subTest(signoff=signoff):
                self.assertFalse(clean_result(self.comment(signoff), "a" * 40))

    def test_inserted_or_trailing_prose_stays_pending(self):
        body = self.comment("Breezy!")
        with_footer = body + CLEAN_RESULT_FOOTER
        for changed in (
            body.replace(
                "**Reviewed commit:**",
                "But I found a blocking issue\n\n**Reviewed commit:**",
            ),
            body + "But I found a blocking issue",
            with_footer.replace("</details>", "But I found a blocking issue</details>"),
            with_footer + "\nBut I found a blocking issue",
        ):
            with self.subTest(body=changed):
                self.assertFalse(clean_result(changed, "a" * 40))

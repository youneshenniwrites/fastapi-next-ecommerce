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
    "Great work, you're ready for round-2!",
    ":thumbs_up:",
)

REJECTED = (
    "Except a blocker!",
    "Swish! But there are issues.",
    "Delightful! But fix this.",
    "You're on a roll. But fix this.",
    ":rocket: But fix this.",
    ":+1: But there are issues.",
    "Nice :+1:",
    ":rocket",
    "🚀",
    "",
    "Nice job. Thanks!",
    "fix!",
    "BUT all good!",
    ":fix:",
    ":+1:",
    "Already looking forward to the next diff.",
    "A" * 41,
    "Nice_work!",
    "Great+work!",
    "Great/work!",
    "Great: work!",
    "Great; work!",
    "Great (work)!",
    "Great! work",
    "Great!!",
)


class CleanVariants(unittest.TestCase):
    def comment(self, signoff, sha="a" * 40, trailer=""):
        """Build a clean-result comment bound to the supplied head and footer."""
        return (
            f"Codex Review: Didn't find any major issues. {signoff}\n\n"
            f"**Reviewed commit:** `{sha[:10]}`{trailer}"
        )

    def test_short_signoffs_pass_with_and_without_footer(self):
        """Accept allowed phrases and tokens only for their reviewed commit."""
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
        """Reject findings, malformed tokens, disallowed characters and long phrases."""
        for signoff in REJECTED:
            with self.subTest(signoff=signoff):
                self.assertFalse(clean_result(self.comment(signoff), "a" * 40))

    def test_signoff_length_boundary(self):
        """Count punctuation and shortcode delimiters toward the 40-character cap."""
        for signoff, too_long in (
            ("A" * 40, "A" * 41),
            ("A" * 39 + "!", "A" * 40 + "!"),
            (":" + "a" * 38 + ":", ":" + "a" * 39 + ":"),
        ):
            for trailer in ("", CLEAN_RESULT_FOOTER):
                with self.subTest(signoff=signoff, footer=bool(trailer)):
                    self.assertTrue(
                        clean_result(self.comment(signoff, trailer=trailer), "a" * 40)
                    )
                    self.assertFalse(
                        clean_result(self.comment(too_long, trailer=trailer), "a" * 40)
                    )

    def test_inserted_or_trailing_prose_stays_pending(self):
        """Reject extra prose before the commit, inside the footer or after it."""
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

import unittest
from unittest.mock import patch

from scripts.codex_review_gate import BOT_ID, details_url, evaluate


class StatusLinks(unittest.TestCase):
    @patch.dict("os.environ", {"GITHUB_RUN_ID": "123"}, clear=True)
    def test_actions_links_to_its_run(self):
        self.assertEqual(
            details_url("owner/repo"), "https://github.com/owner/repo/actions/runs/123"
        )

    @patch.dict("os.environ", {}, clear=True)
    def test_local_requires_real_run(self):
        with self.assertRaises(ValueError):
            details_url("owner/repo")

    def test_rejects_pr_loop(self):
        with self.assertRaises(ValueError):
            details_url("owner/repo", "https://github.com/owner/repo/pull/37")

    def test_local_can_link_evidence_job(self):
        self.assertEqual(
            details_url(
                "owner/repo", "https://github.com/owner/repo/actions/runs/123/job/456"
            ),
            "https://github.com/owner/repo/actions/runs/123/job/456",
        )


class ReviewEvidence(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.bot = {"id": BOT_ID, "type": "Bot"}
        self.request = {
            "id": 10,
            "body": "@codex review\n<!-- codex-review-head:" + self.sha + " -->",
            "created_at": "2026-09-08T10:00:00Z",
            "updated_at": "2026-09-08T10:00:00Z",
        }
        self.summary = {
            "id": 11,
            "user": self.bot,
            "updated_at": "2026-09-08T10:01:00Z",
            "body": "<!-- codex-pull-request-review-summary -->\n| 📝 **Code Review** | ✅ **Completed** | `aaaaaaa` | Manual request |",
        }
        self.reactions = {10: [{"user": self.bot, "content": "+1"}]}

    def result(self, unresolved=False):
        return evaluate(
            self.sha, [self.request, self.summary], self.reactions, unresolved
        )[0]

    def test_edited_request(self):
        self.request["updated_at"] = "2026-09-08T10:02:00Z"
        self.assertEqual(self.result(), "pending")

    def test_clean(self):
        self.assertEqual(self.result(), "success")

    def test_unresolved(self):
        self.assertEqual(self.result(True), "pending")

    def test_spoofed_summary(self):
        self.summary["user"] = {"id": 1, "type": "User"}
        self.assertEqual(self.result(), "pending")

    def test_spoofed_reaction(self):
        self.reactions[10][0]["user"] = {"id": 1, "type": "User"}
        self.assertEqual(self.result(), "pending")

    def test_stale_commit(self):
        self.summary["body"] = self.summary["body"].replace("aaaaaaa", "bbbbbbb")
        self.assertEqual(self.result(), "pending")

    def test_running(self):
        self.summary["body"] = self.summary["body"].replace(
            "✅ **Completed**", "🔄 **Running**"
        )
        self.assertEqual(self.result(), "pending")

    def test_findings_without_clean_signal(self):
        self.reactions = {}
        self.assertEqual(self.result(), "pending")

    def test_stale_summary(self):
        self.summary["updated_at"] = "2026-09-08T09:00:00Z"
        self.assertEqual(self.result(), "pending")

    def test_new_commit_requires_new_request(self):
        self.sha = "b" * 40
        self.assertEqual(self.result(), "pending")

    def test_unknown_format(self):
        self.summary["body"] = "Unexpected"
        self.assertEqual(self.result(), "pending")

    def clean_comment(self):
        return {
            "id": 12,
            "user": self.bot,
            "created_at": "2026-09-08T10:00:59Z",
            "updated_at": "2026-09-08T10:00:59Z",
            "body": "Codex Review: Didn't find any major issues. Can't wait for the next one!\n\n**Reviewed commit:** `aaaaaaaaaa`\n",
        }

    def test_explicit_clean_comment(self):
        self.request["body"] = "@codex review"
        self.assertEqual(
            evaluate(
                self.sha, [self.request, self.summary, self.clean_comment()], {}, False
            )[0],
            "success",
        )

    def test_wrong_head_clean_comment(self):
        comment = self.clean_comment()
        comment["body"] = comment["body"].replace("aaaaaaaaaa", "bbbbbbbbbb")
        self.assertEqual(
            evaluate(self.sha, [self.request, self.summary, comment], {}, False)[0],
            "pending",
        )

    def test_forged_clean_comment(self):
        comment = self.clean_comment()
        comment["user"] = {"id": 1, "type": "User"}
        self.assertEqual(
            evaluate(self.sha, [self.request, self.summary, comment], {}, False)[0],
            "pending",
        )

    def test_new_unmarked_request_invalidates_old_reaction(self):
        newer = dict(
            self.request,
            id=13,
            body="@codex review",
            created_at="2026-09-08T10:02:00Z",
            updated_at="2026-09-08T10:02:00Z",
        )
        self.assertEqual(
            evaluate(
                self.sha, [self.request, self.summary, newer], self.reactions, False
            )[0],
            "pending",
        )

    def test_later_findings_invalidate_clean_comment(self):
        review = {
            "user": self.bot,
            "submitted_at": "2026-09-08T10:01:00Z",
            "state": "COMMENTED",
        }
        self.assertEqual(
            evaluate(
                self.sha,
                [self.request, self.summary, self.clean_comment()],
                {},
                False,
                [review],
            )[0],
            "pending",
        )


if __name__ == "__main__":
    unittest.main()

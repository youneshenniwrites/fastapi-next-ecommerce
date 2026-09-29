import unittest
from unittest.mock import patch

from scripts import coderabbit_review_gate as gate


class CodeRabbitEvidence(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.approval = {
            "user": {"id": gate.BOT_ID, "type": "Bot"},
            "state": "APPROVED",
            "commit_id": self.sha,
            "submitted_at": "2026-09-29T10:00:00Z",
        }

    def test_exact_head_approval(self):
        self.assertEqual(gate.assess(self.sha, [self.approval], False)[0], "success")

    def test_missing_stale_spoofed_or_skipped_approval(self):
        variants = [
            [],
            [{**self.approval, "commit_id": "b" * 40}],
            [{**self.approval, "user": {"id": 1, "type": "Bot"}}],
            [{**self.approval, "user": {"id": gate.BOT_ID, "type": "User"}}],
            [{**self.approval, "state": "COMMENTED", "body": "Review skipped"}],
            [{**self.approval, "state": "DISMISSED"}],
            [{**self.approval, "submitted_at": None}],
        ]
        for reviews in variants:
            with self.subTest(reviews=reviews):
                self.assertEqual(gate.assess(self.sha, reviews, False)[0], "pending")

    def test_unresolved_threads_block_approval(self):
        self.assertEqual(gate.assess(self.sha, [self.approval], True)[0], "pending")

    def test_later_or_edited_findings_block_even_resolved_threads(self):
        for state in ("COMMENTED", "CHANGES_REQUESTED", "DISMISSED"):
            finding = {
                **self.approval,
                "state": state,
                "submitted_at": "2026-09-29T09:00:00Z",
                "updated_at": "2026-09-29T10:01:00Z",
            }
            with self.subTest(state=state):
                self.assertEqual(
                    gate.assess(self.sha, [self.approval], False, [finding])[0],
                    "pending",
                )

    def test_old_findings_allow_fresh_approval(self):
        finding = {
            **self.approval,
            "state": "CHANGES_REQUESTED",
            "submitted_at": "2026-09-29T09:00:00Z",
        }
        self.assertEqual(
            gate.assess(self.sha, [finding, self.approval], False)[0], "success"
        )

    def test_equal_time_or_missing_time_findings_fail_closed(self):
        for timestamp in (None, self.approval["submitted_at"]):
            finding = {**self.approval, "state": "COMMENTED", "submitted_at": timestamp}
            self.assertEqual(
                gate.assess(self.sha, [self.approval], False, [finding])[0], "pending"
            )

    def test_outsider_comment_cannot_invalidate_approval(self):
        finding = {**self.approval, "state": "COMMENTED", "user": {"id": 1}}
        self.assertEqual(
            gate.assess(self.sha, [self.approval], False, [finding])[0], "success"
        )

    def test_inspect_rejects_head_race_and_closed_or_draft(self):
        original = {"head": {"sha": self.sha}, "state": "open", "draft": False}
        for current in (
            {**original, "head": {"sha": "b" * 40}},
            {**original, "draft": True},
            {**original, "state": "closed"},
        ):
            with (
                patch.object(gate.evidence, "api", side_effect=[original, current]),
                patch.object(gate.evidence, "pages", return_value=[self.approval]),
                patch.object(gate.evidence, "review_history", return_value=[]),
                patch.object(gate.evidence, "threads", return_value=False),
            ):
                self.assertEqual(gate.inspect("owner/repo", 1)[1], "pending")

    def test_incomplete_evidence_propagates_failure(self):
        with (
            patch.object(
                gate.evidence, "api", return_value={"head": {"sha": self.sha}}
            ),
            patch.object(
                gate.evidence, "pages", side_effect=RuntimeError("pagination")
            ),
            self.assertRaises(RuntimeError),
        ):
            gate.inspect("owner/repo", 1)

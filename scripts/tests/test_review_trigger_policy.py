"""Verify review refresh routes and recovery without executing PR code."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def event_types(text, event):
    section = re.search(
        rf"^  {event}:\n(.*?)(?=^  \w|^permissions:)", text, re.MULTILINE | re.DOTALL
    )
    if not section:
        return set()
    types = re.search(r"types: \[([^\]]+)\]", section[1])
    return {item.strip() for item in types[1].split(",")} if types else set()


class ReviewTriggerPolicyTests(unittest.TestCase):
    def setUp(self):
        self.gate = (ROOT / ".github/workflows/codex-review.yml").read_text()
        self.relay = (ROOT / ".github/workflows/codex-review-events.yml").read_text()

    def test_one_refresh_for_a_relay_lifecycle_including_failed_completion(self):
        # A completed relay signals fresh API inspection, regardless of result.
        configured = event_types(self.gate, "workflow_run")
        delivered = [
            action for action in ("requested", "completed") if action in configured
        ]
        self.assertEqual(delivered, ["completed"])
        self.assertNotIn("github.event.workflow_run.conclusion", self.gate)

    def test_submitted_edited_dismissed_and_inline_changes_still_refresh(self):
        self.assertEqual(
            event_types(self.relay, "pull_request_review"),
            {"submitted", "edited", "dismissed"},
        )
        self.assertEqual(
            event_types(self.relay, "pull_request_review_comment"),
            {"created", "edited", "deleted"},
        )
        self.assertIn("workflows: [Codex review events]", self.gate)
        self.assertIn("completed", event_types(self.gate, "workflow_run"))

    def test_head_request_and_recovery_routes_remain(self):
        self.assertTrue(
            {"synchronize", "reopened", "edited", "closed"}.issubset(
                event_types(self.gate, "pull_request_target")
            )
        )
        self.assertEqual(
            event_types(self.gate, "issue_comment"), {"created", "edited", "deleted"}
        )
        self.assertIn("cron: '*/5 * * * *'", self.gate)
        self.assertIn("workflow_dispatch:", self.gate)

    def test_trusted_execution_and_dependency_completion_remain(self):
        self.assertIn("permissions: {}", self.relay)
        self.assertNotIn("uses:", self.relay)
        self.assertIn("ref: ${{ github.event.repository.default_branch }}", self.gate)
        self.assertNotIn("github.event.pull_request.head", self.gate)
        continuation = (
            ROOT / ".github/workflows/dependabot-continuation.yml"
        ).read_text()
        self.assertIn("Codex review gate", continuation)
        self.assertIn("types: [completed]", continuation)
        self.assertNotIn("Dependabot continuation]", continuation)

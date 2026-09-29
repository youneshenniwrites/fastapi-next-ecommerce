import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from coderabbit_retry import may_request
from dependabot_reconcile import review_request


class RetryTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.request = {
            "author_association": "OWNER",
            "body": f"@coderabbitai review\n<!-- coderabbit-review-head:{self.sha} -->",
            "created_at": "2026-09-29T10:00:00Z",
        }
        self.response = {
            "user": {"id": 136622811, "type": "Bot"},
            "body": "## Review limit reached\nNext included review available in 45 minutes.",
            "updated_at": "2026-09-29T10:01:00Z",
        }
        self.now = datetime(2026, 9, 29, 11, 2, tzinfo=timezone.utc)

    def allowed(self, comments):
        return may_request(comments, self.sha, review_request, self.now)

    def test_initial_request(self):
        self.assertTrue(self.allowed([]))

    def test_no_response_is_not_retry_permission(self):
        self.assertFalse(self.allowed([self.request]))

    def test_trusted_limit_retries_only_after_cooldown(self):
        self.assertTrue(self.allowed([self.request, self.response]))
        self.now = self.now.replace(hour=10)
        self.assertFalse(self.allowed([self.request, self.response]))

    def test_longer_advertised_delay_is_respected(self):
        self.response["body"] = (
            "## Review limit reached\nNext included review available in 180 minutes."
        )
        self.assertFalse(self.allowed([self.request, self.response]))

    def test_untrusted_notice_rejected(self):
        self.response["user"]["id"] = 1
        self.assertFalse(self.allowed([self.request, self.response]))

    def test_attempt_cap(self):
        self.assertFalse(self.allowed([self.request] * 3 + [self.response]))

    def test_notice_before_latest_request_cannot_retry_it(self):
        self.request["created_at"] = "2026-09-29T10:02:00Z"
        self.assertFalse(self.allowed([self.request, self.response]))

    def test_newer_activity_supersedes_limit(self):
        newer = {
            **self.response,
            "updated_at": "2026-09-29T10:03:00Z",
            "body": "Review triggered.",
        }
        self.assertFalse(self.allowed([self.request, self.response, newer]))

    def test_unknown_delay_waits_a_day(self):
        self.response["body"] = "Review rate limited."
        self.assertFalse(self.allowed([self.request, self.response]))
        self.now = self.now.replace(day=30)
        self.assertTrue(self.allowed([self.request, self.response]))

    def test_bad_timestamp_blocks_retry(self):
        self.request["created_at"] = "invalid"
        self.assertFalse(self.allowed([self.request, self.response]))

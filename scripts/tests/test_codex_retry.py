"""Quota recovery must never turn untrusted or stale activity into requests."""

import unittest
from datetime import datetime, timedelta, timezone

from scripts.codex_retry import QUOTA_NOTICE, may_request
from scripts.codex_review_gate import BOT_ID


class QuotaRetryTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.start = datetime(2026, 10, 5, tzinfo=timezone.utc)
        self.request = self.make_request(1, self.start)
        self.response = self.make_response(2, self.start + timedelta(minutes=1))

    def make_request(self, number, time):
        return {
            "id": number,
            "author_association": "OWNER",
            "body": f"@codex review\n<!-- codex-review-head:{self.sha} -->",
            "created_at": time.isoformat(),
            "updated_at": time.isoformat(),
        }

    def make_response(self, number, time):
        return {
            "id": number,
            "user": {"id": BOT_ID, "type": "Bot"},
            "body": QUOTA_NOTICE,
            "created_at": time.isoformat(),
            "updated_at": time.isoformat(),
        }

    def allowed(self, comments=None, **kwargs):
        return may_request(
            [self.request, self.response] if comments is None else comments,
            self.sha,
            now=self.start + timedelta(days=10),
            **kwargs,
        )

    def test_initial_request_then_wait_without_quota_response(self):
        self.assertTrue(self.allowed([]))
        self.assertFalse(self.allowed([self.request]))

    def test_only_observed_trusted_unedited_quota_notice_allows_retry(self):
        self.assertTrue(self.allowed())
        for changes in (
            {"user": {"id": 1, "type": "Bot"}},
            {"user": {"id": BOT_ID, "type": "User"}},
            {"body": QUOTA_NOTICE + " Buy credits."},
            {"body": "Codex is unavailable"},
            {"updated_at": "2026-10-06T01:00:00Z"},
            {"updated_at": "unknown"},
        ):
            with self.subTest(changes=changes):
                self.assertFalse(self.allowed([self.request, self.response | changes]))

    def test_first_retry_waits_24_hours_after_response(self):
        response_time = self.start + timedelta(minutes=1)
        self.assertFalse(
            may_request(
                [self.request, self.response],
                self.sha,
                now=response_time + timedelta(hours=24) - timedelta(seconds=1),
            )
        )
        self.assertTrue(
            may_request(
                [self.request, self.response],
                self.sha,
                now=response_time + timedelta(hours=24),
            )
        )

    def test_second_retry_waits_seven_days_and_third_is_never_allowed(self):
        request2 = self.make_request(3, self.start + timedelta(days=2))
        response2 = self.make_response(4, self.start + timedelta(days=2, minutes=1))
        comments = [self.request, self.response, request2, response2]
        self.assertFalse(
            may_request(comments, self.sha, now=self.start + timedelta(days=3))
        )
        self.assertTrue(self.allowed(comments))
        comments.append(self.make_request(5, self.start + timedelta(days=10)))
        comments.append(
            self.make_response(6, self.start + timedelta(days=10, minutes=1))
        )
        self.assertFalse(
            may_request(comments, self.sha, now=self.start + timedelta(days=30))
        )

    def test_later_summary_or_findings_supersede_quota(self):
        for body in ("<!-- codex-pull-request-review-summary -->", "Please fix this"):
            activity = self.make_response(3, self.start + timedelta(hours=1)) | {
                "body": body
            }
            self.assertFalse(self.allowed([self.request, self.response, activity]))

    def test_later_formal_or_edited_review_supersedes_quota(self):
        review = {
            "user": {"id": BOT_ID, "type": "Bot"},
            "submitted_at": self.start.isoformat(),
            "updated_at": (self.start + timedelta(hours=1)).isoformat(),
        }
        self.assertFalse(self.allowed(reviews=[review]))

    def test_newer_manual_request_owns_review(self):
        request = self.make_request(3, self.start + timedelta(hours=1)) | {
            "body": "@codex review"
        }
        self.assertFalse(self.allowed([self.request, self.response, request]))

    def test_initial_bare_request_suppresses_automation_before_summary_exists(self):
        bare = self.request | {"body": "@codex review"}
        self.assertFalse(self.allowed([bare]))
        self.assertFalse(self.allowed([bare, self.response]))

    def test_outsider_bare_request_does_not_suppress_automation(self):
        bare = self.request | {"body": "@codex review", "author_association": "NONE"}
        self.assertTrue(self.allowed([bare]))

    def test_marker_stripped_by_edit_suppresses_automation(self):
        bare = self.request | {
            "body": "@codex review",
            "updated_at": (self.start + timedelta(days=3)).isoformat(),
        }
        self.assertFalse(self.allowed([bare]))
        newer = self.make_request(3, self.start + timedelta(days=2))
        response = self.make_response(4, self.start + timedelta(days=2, minutes=1))
        self.assertFalse(self.allowed([bare, newer, response]))

    def test_newer_unedited_bound_request_supersedes_bare_request(self):
        bare = self.request | {"body": "@codex review"}
        newer = self.make_request(3, self.start + timedelta(days=2))
        response = self.make_response(4, self.start + timedelta(days=2, minutes=1))
        self.assertFalse(self.allowed([bare, newer]))
        self.assertTrue(self.allowed([bare, newer, response]))
        self.sha = "b" * 40
        self.assertTrue(self.allowed([bare, newer, response]))

    def test_edited_bound_request_cannot_supersede_bare_request(self):
        bare = self.request | {"body": "@codex review"}
        newer = self.make_request(3, self.start + timedelta(days=2)) | {
            "updated_at": (self.start + timedelta(days=3)).isoformat(),
        }
        self.sha = "b" * 40
        self.assertFalse(self.allowed([bare, newer]))

    def test_stale_quota_and_missing_or_edited_request_times_do_not_retry(self):
        self.assertFalse(
            self.allowed(
                [self.request, self.make_response(0, self.start - timedelta(days=1))]
            )
        )
        for changes in ({"created_at": None}, {"updated_at": "2026-10-06T00:00:00Z"}):
            self.assertFalse(self.allowed([self.request | changes, self.response]))

    def test_outsider_cannot_consume_head_request_budget(self):
        self.assertTrue(self.allowed([self.request | {"author_association": "NONE"}]))

    def test_new_head_gets_initial_request(self):
        self.sha = "b" * 40
        self.assertTrue(self.allowed())

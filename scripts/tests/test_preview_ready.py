"""Reject unsafe sources and stale CI before deployment credentials are read."""

import copy
import unittest
from unittest.mock import patch

from scripts import preview_ready as preview

SHA = "a" * 40
REPO = "owner/repo"
PR = {
    "state": "open",
    "draft": False,
    "head": {"sha": SHA, "repo": {"full_name": REPO}},
    "base": {"ref": "main", "repo": {"full_name": REPO}},
    "changed_files": 1,
}


class PreviewEligibilityTests(unittest.TestCase):
    def test_source_boundary(self):
        self.assertTrue(preview.source_allowed(PR, REPO, SHA))
        for field, value in [("draft", True), ("state", "closed")]:
            altered = {**PR, field: value}
            self.assertFalse(preview.source_allowed(altered, REPO, SHA))
        for field in ["head", "base"]:
            altered = copy.deepcopy(PR)
            altered[field]["repo"]["full_name"] = "attacker/fork"
            self.assertFalse(preview.source_allowed(altered, REPO, SHA))
        self.assertFalse(preview.source_allowed(PR, REPO, "b" * 40))
        self.assertFalse(preview.source_allowed(PR, REPO, "main"))

    def test_latest_exact_pr_ci(self):
        good = {
            "id": 1,
            "head_sha": SHA,
            "event": "pull_request",
            "pull_requests": [{"number": 45}],
            "conclusion": "success",
        }
        self.assertTrue(preview.passed([good], SHA, 45))
        for mutation in [
            {"id": 2, "conclusion": "failure"},
            {"id": 2, "conclusion": None},
        ]:
            self.assertFalse(preview.passed([good, {**good, **mutation}], SHA, 45))
        for mutation in [
            {"head_sha": "b" * 40},
            {"event": "push"},
            {"pull_requests": []},
        ]:
            self.assertFalse(preview.passed([{**good, **mutation}], SHA, 45))
        self.assertFalse(preview.passed([], SHA, 45))

    @patch.dict("os.environ", {"GITHUB_REF": "refs/heads/main"})
    @patch.object(
        preview.codex,
        "pages",
        return_value=[{"filename": "frontend/src/lib/session.ts"}],
    )
    @patch.object(preview.codex, "inspect", return_value=(SHA, "success", "clean"))
    @patch.object(preview.codex, "api")
    def test_success_and_changed_head_before_upload(self, api, inspect, pages):
        run = {
            "id": 1,
            "head_sha": SHA,
            "event": "pull_request",
            "pull_requests": [{"number": 45}],
            "conclusion": "success",
        }
        api.side_effect = [
            PR,
            *[{"workflow_runs": [run]} for _ in preview.WORKFLOWS],
            PR,
        ]
        self.assertEqual(preview.verify(REPO, 45, SHA), SHA)
        changed = copy.deepcopy(PR)
        changed["head"]["sha"] = "b" * 40
        api.side_effect = [
            PR,
            *[{"workflow_runs": [run]} for _ in preview.WORKFLOWS],
            changed,
        ]
        with self.assertRaisesRegex(ValueError, "changed"):
            preview.verify(REPO, 45, SHA)
        api.side_effect = [PR, {"workflow_runs": []}]
        with self.assertRaisesRegex(ValueError, "CI"):
            preview.verify(REPO, 45, SHA)

    @patch.dict("os.environ", {"GITHUB_REF": "refs/heads/feature"})
    @patch.object(preview.codex, "api")
    def test_non_main_reads_no_evidence(self, api):
        with self.assertRaises(ValueError):
            preview.verify(REPO, 45, SHA)
        api.assert_not_called()

    @patch.dict("os.environ", {"GITHUB_REF": "refs/heads/main"})
    @patch.object(
        preview.codex,
        "pages",
        return_value=[{"filename": "frontend/src/lib/session.ts"}],
    )
    @patch.object(preview.codex, "inspect")
    @patch.object(preview.codex, "api", return_value=PR)
    def test_missing_or_stale_review_stops_before_ci(self, api, inspect, pages):
        for result in [(SHA, "pending", "unknown"), ("b" * 40, "success", "clean")]:
            inspect.return_value = result
            with self.assertRaises(ValueError):
                preview.verify(REPO, 45, SHA)
            self.assertEqual(api.call_args.args, ("repos/owner/repo/pulls/45",))


if __name__ == "__main__":
    unittest.main()

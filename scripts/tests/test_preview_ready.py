"""Reject unsafe sources and stale CI before deployment credentials are read."""

import copy
import unittest
from unittest.mock import patch

from scripts import preview_ready as preview

SHA = "a" * 40
MAIN_SHA = "b" * 40
REPO = "owner/repo"
PR = {
    "state": "open",
    "draft": False,
    "head": {"sha": SHA, "repo": {"full_name": REPO}},
    "base": {"ref": "main", "repo": {"full_name": REPO}},
    "changed_files": 1,
}


class PreviewEligibilityTests(unittest.TestCase):
    def evidence(
        self,
        api,
        *,
        bases=(MAIN_SHA, MAIN_SHA),
        prs=(PR, PR),
        comparison=None,
        ci=True,
    ):
        base_reads = iter(bases)
        pr_reads = iter(prs)
        run = {
            "id": 1,
            "head_sha": SHA,
            "event": "pull_request",
            "pull_requests": [{"number": 45}],
            "conclusion": "success",
        }

        def response(path):
            if path == f"repos/{REPO}/pulls/45":
                return next(pr_reads)
            if path == f"repos/{REPO}/git/ref/heads/main":
                return {"object": {"type": "commit", "sha": next(base_reads)}}
            if path == f"repos/{REPO}/compare/{bases[0]}...{SHA}":
                if comparison is not None:
                    return comparison
                return {
                    "status": "ahead",
                    "base_commit": {"sha": bases[0]},
                    "merge_base_commit": {"sha": bases[0]},
                }
            if path.startswith(f"repos/{REPO}/actions/workflows/"):
                return {"workflow_runs": [run] if ci else []}
            self.fail(f"Unexpected evidence request: {path}")

        api.side_effect = response

    @patch.dict("os.environ", {"GITHUB_REF": "refs/heads/main"})
    @patch.object(
        preview.codex,
        "pages",
        return_value=[{"filename": "frontend/src/lib/session.ts"}],
    )
    @patch.object(preview.codex, "inspect", return_value=(SHA, "success", "clean"))
    @patch.object(preview.codex, "api")
    def test_behind_main_rejected_despite_successful_head_review_and_ci(
        self, api, inspect, pages
    ):
        for status in ["diverged", "behind"]:
            with self.subTest(status=status):
                self.evidence(
                    api,
                    comparison={
                        "status": status,
                        "base_commit": {"sha": MAIN_SHA},
                        "merge_base_commit": {"sha": "c" * 40},
                    },
                )
                with self.assertRaisesRegex(ValueError, "main"):
                    preview.verify(REPO, 45, SHA)
        inspect.assert_not_called()

    @patch.dict("os.environ", {"GITHUB_REF": "refs/heads/main"})
    @patch.object(
        preview.codex,
        "pages",
        return_value=[{"filename": "frontend/src/lib/session.ts"}],
    )
    @patch.object(preview.codex, "inspect", return_value=(SHA, "success", "clean"))
    @patch.object(preview.codex, "api")
    def test_unchanged_head_rejected_when_main_advances_during_evidence(
        self, api, inspect, pages
    ):
        self.evidence(api, bases=(MAIN_SHA, "c" * 40))
        with self.assertRaisesRegex(ValueError, "main.*changed"):
            preview.verify(REPO, 45, SHA)

    @patch.dict("os.environ", {"GITHUB_REF": "refs/heads/main"})
    @patch.object(
        preview.codex,
        "pages",
        return_value=[{"filename": "frontend/src/lib/session.ts"}],
    )
    @patch.object(preview.codex, "inspect", return_value=(SHA, "success", "clean"))
    @patch.object(preview.codex, "api")
    def test_second_verification_rejects_same_head_after_main_advances(
        self, api, inspect, pages
    ):
        self.evidence(api)
        self.assertEqual(preview.verify(REPO, 45, SHA), SHA)
        self.evidence(
            api,
            bases=("c" * 40,),
            comparison={
                "status": "diverged",
                "base_commit": {"sha": "c" * 40},
                "merge_base_commit": {"sha": MAIN_SHA},
            },
        )
        with self.assertRaisesRegex(ValueError, "main"):
            preview.verify(REPO, 45, SHA)

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
        self.evidence(api)
        self.assertEqual(preview.verify(REPO, 45, SHA), SHA)
        requested = [call.args[0] for call in api.call_args_list]
        self.assertEqual(requested.count(f"repos/{REPO}/git/ref/heads/main"), 2)
        self.assertIn(f"repos/{REPO}/compare/{MAIN_SHA}...{SHA}", requested)
        for workflow in preview.WORKFLOWS:
            self.assertIn(
                f"repos/{REPO}/actions/workflows/{workflow}/runs?head_sha={SHA}&event=pull_request&per_page=100",
                requested,
            )
        self.evidence(
            api,
            bases=(SHA, SHA),
            comparison={
                "status": "identical",
                "base_commit": {"sha": SHA},
                "merge_base_commit": {"sha": SHA},
            },
        )
        self.assertEqual(preview.verify(REPO, 45, SHA), SHA)
        changed = copy.deepcopy(PR)
        changed["head"]["sha"] = "b" * 40
        self.evidence(api, prs=(PR, changed))
        with self.assertRaisesRegex(ValueError, "changed"):
            preview.verify(REPO, 45, SHA)
        self.evidence(api, ci=False)
        with self.assertRaisesRegex(ValueError, "CI"):
            preview.verify(REPO, 45, SHA)

    @patch.dict("os.environ", {"GITHUB_REF": "refs/heads/main"})
    @patch.object(preview.codex, "inspect")
    @patch.object(preview.codex, "api")
    def test_incomplete_or_mismatched_ancestry_never_accepts_ci(self, api, inspect):
        valid = {
            "status": "ahead",
            "base_commit": {"sha": MAIN_SHA},
            "merge_base_commit": {"sha": MAIN_SHA},
        }
        for comparison in [
            {},
            {**valid, "status": "unknown"},
            {**valid, "base_commit": {"sha": "c" * 40}},
            {**valid, "merge_base_commit": {"sha": "c" * 40}},
            {**valid, "merge_base_commit": None},
        ]:
            with self.subTest(comparison=comparison):
                self.evidence(api, comparison=comparison)
                with self.assertRaisesRegex(ValueError, "main"):
                    preview.verify(REPO, 45, SHA)
        inspect.assert_not_called()

    @patch.object(preview.codex, "api")
    def test_main_requires_current_commit_evidence(self, api):
        for evidence in [{}, {"type": "tag", "sha": MAIN_SHA}, {"sha": "main"}]:
            with self.subTest(evidence=evidence):
                api.return_value = {"object": evidence}
                with self.assertRaisesRegex(ValueError, "main"):
                    preview.main_revision(REPO)

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
    @patch.object(preview.codex, "api")
    def test_missing_or_stale_review_stops_before_ci(self, api, inspect, pages):
        for result in [(SHA, "pending", "unknown"), ("b" * 40, "success", "clean")]:
            self.evidence(api)
            inspect.return_value = result
            with self.assertRaises(ValueError):
                preview.verify(REPO, 45, SHA)
            self.assertFalse(
                any("/actions/" in call.args[0] for call in api.call_args_list)
            )


if __name__ == "__main__":
    unittest.main()

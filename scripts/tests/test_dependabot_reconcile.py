"""Regression tests for serial, exact-head continuation."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dependabot_reconcile import reconcile


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self.pr = {
            "number": 1,
            "state": "open",
            "draft": False,
            "user": {"login": "dependabot[bot]"},
            "base": {"ref": "main"},
            "head": {
                "sha": "a" * 40,
                "repo": {"full_name": "owner/repo"},
                "ref": "dependabot/npm/update",
            },
            "mergeable_state": "clean",
        }
        self.calls = []
        self.comments = [
            {
                "author_association": "OWNER",
                "body": "@codex review\n<!-- codex-review-head:" + "a" * 40 + " -->",
            }
        ]
        self.state = "success"
        self.reason = "pending review"
        self.states = ["SUCCESS"]
        self.reads = 0
        self.mutate = lambda: None

    def api(self, path, **fields):
        self.calls.append((path, fields))
        if fields:
            return {"merged": True}
        self.reads += 1
        self.mutate()
        return copy.deepcopy(self.pr)

    def run_reconcile(self, token=True, count=1, repair=None):
        return reconcile(
            "owner/repo",
            [{**self.pr, "number": n + 1} for n in range(count)],
            self.api,
            lambda p: self.comments if p.endswith("/comments") else [],
            lambda n: self.states,
            lambda r, n: ("a" * 40, self.state, self.reason),
            self.api if token else None,
            repair=repair,
        )

    def writes(self):
        return [(p, f) for p, f in self.calls if f]

    def test_merges_only_one_exact_head(self):
        self.run_reconcile(count=3)
        self.assertEqual(len(self.writes()), 2)
        self.assertEqual(self.writes()[-1][1]["sha"], "a" * 40)

    def test_behind_updates_only_one_atomically(self):
        self.pr["mergeable_state"] = "behind"
        self.run_reconcile(count=3)
        self.assertEqual(
            self.writes(),
            [
                (
                    "repos/owner/repo/pulls/1/update-branch",
                    {"method": "PUT", "expected_head_sha": "a" * 40},
                )
            ],
        )

    def test_missing_token_never_updates_branch(self):
        self.pr["mergeable_state"] = "behind"
        self.run_reconcile(token=False)
        self.assertEqual(self.writes(), [])

    def test_stale_review_and_failed_ci_block(self):
        self.state = "pending"
        self.run_reconcile()
        self.assertEqual(self.writes(), [])
        self.state = "success"
        for states in [[], ["FAILURE"], ["PENDING"], ["CANCELLED"]]:
            self.states = states
            self.run_reconcile()
            self.assertEqual(self.writes(), [])

    def test_changed_head_or_base_blocks_approval(self):
        for key in ["head", "base"]:
            self.setUp()

            def mutate(key=key):
                if self.reads == 2:
                    self.pr[key]["sha" if key == "head" else "ref"] = "changed"

            self.mutate = mutate
            self.run_reconcile()
            self.assertEqual(self.writes(), [])

    def test_untrusted_fork_ignored(self):
        self.pr["head"]["repo"]["full_name"] = "fork/repo"
        self.run_reconcile()
        self.assertEqual(self.writes(), [])

    def test_request_is_idempotent_for_current_head(self):
        self.state = "pending"
        self.run_reconcile()
        self.assertEqual(self.writes(), [])
        self.comments = []
        self.run_reconcile()
        self.assertEqual(
            self.writes()[0][1]["body"],
            "@codex review\n<!-- codex-review-head:" + "a" * 40 + " -->",
        )

    def test_new_findings_before_merge_block(self):
        def mutate():
            if self.reads == 2:
                self.state = "pending"

        self.mutate = mutate
        self.run_reconcile()
        self.assertTrue(all(not p.endswith("/merge") for p, f in self.writes()))

    def test_pending_candidate_prevents_updates_to_later_prs(self):
        self.states = ["PENDING"]
        self.run_reconcile(count=3)
        self.assertEqual(self.reads, 1)
        self.assertEqual(self.writes(), [])

    def test_failed_ci_never_requests_paid_review(self):
        self.comments = []
        self.states = ["FAILURE"]
        self.run_reconcile()
        self.assertEqual(self.writes(), [])

    def test_missing_member_token_never_merges(self):
        self.run_reconcile(token=False)
        self.assertEqual(self.writes(), [])

    def test_nonclean_protection_blocks_merge_even_with_green_checks(self):
        self.pr["mergeable_state"] = "blocked"
        self.run_reconcile()
        self.assertTrue(all(not p.endswith("/merge") for p, f in self.writes()))

    def test_privileged_workflows_only_checkout_main(self):
        root = Path(__file__).resolve().parents[2]
        for name in ("dependabot-auto-merge.yml", "dependabot-continuation.yml"):
            workflow = (root / ".github" / "workflows" / name).read_text()
            self.assertIn("ref: main", workflow)
            self.assertIn("group: dependabot-protected-merge", workflow)
            self.assertNotIn("download-artifact", workflow)
            self.assertNotIn("pull_request.head", workflow)
        continuation = (
            root / ".github/workflows/dependabot-continuation.yml"
        ).read_text()
        self.assertNotIn("workflows: [Dependabot continuation", continuation)

    def test_explicit_findings_skip_to_next_queue_candidate(self):
        self.state = "pending"
        self.reason = "Resolve review conversations and obtain a clean re-review"
        self.run_reconcile(count=3)
        self.assertEqual(self.reads, 3)
        self.assertEqual(self.writes(), [])

    def test_export_repair_precedes_failed_ci_and_stops_queue(self):
        self.states = ["FAILURE"]
        calls = []

        def repair(*args):
            calls.append(args)
            return True

        result = self.run_reconcile(count=3, repair=repair)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.reads, 1)
        self.assertIn("Repaired Python export", result[0][1])
        self.assertEqual(self.writes(), [])

    def test_unsafe_export_never_requests_review_or_merges(self):
        from dependabot_export import ExportNotSafe

        def repair(*args):
            raise ExportNotSafe("Untrusted config")

        result = self.run_reconcile(repair=repair)
        self.assertIn("Export repair blocked", result[0][1])
        self.assertEqual(self.writes(), [])


class CheckStatesTests(unittest.TestCase):
    def checks(self, required, all_checks):
        import json
        from types import SimpleNamespace

        from dependabot_reconcile import check_states

        def run(command, **kwargs):
            return SimpleNamespace(
                stdout=json.dumps(required if "--required" in command else all_checks)
            )

        return check_states("owner/repo", 1, run)

    def test_nonrequired_failure_is_preserved(self):
        required = [{"name": "Build", "state": "SUCCESS", "workflow": "Backend CI"}]
        additional = [
            {
                "name": "Coverage",
                "state": "FAILURE",
                "workflow": "PR coverage comparison",
            }
        ]
        self.assertEqual(
            self.checks(required, required + additional),
            ["SUCCESS", "SUCCESS", "FAILURE"],
        )

    def test_informational_codex_and_queue_do_not_deadlock_ci(self):
        required = [{"name": "Build", "state": "SUCCESS", "workflow": "Backend CI"}]
        informational = [
            {"name": "Codex review", "state": "PENDING", "workflow": ""},
            {
                "name": "reconcile",
                "state": "IN_PROGRESS",
                "workflow": "Dependabot continuation",
            },
        ]
        self.assertEqual(
            self.checks(required, required + informational), ["SUCCESS", "SUCCESS"]
        )

    def test_explicit_required_context_is_never_ignored(self):
        codex = [{"name": "Codex review", "state": "PENDING", "workflow": ""}]
        self.assertEqual(self.checks(codex, codex), ["PENDING"])

    def test_missing_required_evidence_is_not_replaced_by_green_optional_ci(self):
        self.assertEqual(
            self.checks(
                [], [{"name": "Build", "state": "SUCCESS", "workflow": "Backend CI"}]
            ),
            [],
        )

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

    def test_existing_approval_does_not_request_another_review(self):
        self.comments = []
        self.run_reconcile()
        self.assertTrue(any(p.endswith("/merge") for p, f in self.writes()))
        self.assertFalse(any(p.endswith("/comments") for p, f in self.writes()))

    def test_findings_without_marker_do_not_request_review_or_stall_queue(self):
        for reason in (
            "Resolve review conversations and obtain a clean re-review",
            "Obtain a new clean review after the latest review findings",
        ):
            self.setUp()
            self.comments = []
            self.state = "pending"
            self.reason = reason
            self.run_reconcile(count=3)
            self.assertEqual(self.writes(), [])
            self.assertEqual(self.reads, 3)

    def test_running_review_does_not_request_another_review(self):
        self.comments = []
        self.state = "pending"
        self.reason = "Codex review is running or has not completed successfully"
        self.run_reconcile()
        self.assertEqual(self.writes(), [])

    def test_quota_stopped_review_retries_then_deduplicates(self):
        from codex_retry import QUOTA_NOTICE
        from codex_review_gate import BOT_ID

        self.state = "pending"
        self.reason = "Codex review is running or has not completed successfully"
        self.comments[0].update(
            id=1,
            created_at="2020-01-01T00:00:00Z",
            updated_at="2020-01-01T00:00:00Z",
        )
        self.comments.append(
            {
                "id": 2,
                "user": {"id": BOT_ID, "type": "Bot"},
                "body": QUOTA_NOTICE,
                "created_at": "2020-01-01T00:01:00Z",
                "updated_at": "2020-01-01T00:01:00Z",
            }
        )
        self.run_reconcile()
        self.assertEqual(len(self.writes()), 1)
        self.comments.append(
            {
                **self.comments[0],
                "id": 3,
                "body": self.writes()[0][1]["body"],
                "created_at": "2020-01-02T00:02:00Z",
                "updated_at": "2020-01-02T00:02:00Z",
            }
        )
        self.calls = []
        self.run_reconcile()
        self.assertEqual(self.writes(), [])

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

    def test_behind_updates_before_unsafe_export_or_stale_failed_ci(self):
        self.pr["mergeable_state"] = "behind"
        self.states = ["FAILURE"]

        def repair(*args):
            self.fail("Export must wait for the synchronized manifest")

        self.run_reconcile(repair=repair)
        self.assertEqual(len(self.writes()), 1)
        self.assertTrue(self.writes()[0][0].endswith("/update-branch"))

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

    def test_coderabbit_request_does_not_consume_codex_request(self):
        self.state = "pending"
        self.comments[0]["body"] = (
            self.comments[0]["body"]
            .replace("@codex review", "@coderabbitai review")
            .replace("codex-review-head:", "coderabbit-review-head:")
        )
        self.run_reconcile()
        self.assertEqual(len(self.writes()), 1)
        self.assertTrue(self.writes()[0][1]["body"].startswith("@codex review\n"))

    def test_head_change_before_review_request_does_not_consume_allowance(self):
        self.state = "pending"
        self.comments = []

        def mutate():
            if self.reads == 2:
                self.pr["head"]["sha"] = "b" * 40

        self.mutate = mutate
        self.run_reconcile()
        self.assertEqual(self.writes(), [])

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

    def test_failed_ci_never_consumes_review_allowance(self):
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


class ApprovalLifecycleTests(unittest.TestCase):
    def setUp(self):
        from dependabot_reconcile import APPROVAL

        self.body = APPROVAL
        self.sha = "a" * 40
        self.pr = {
            "number": 1,
            "state": "open",
            "draft": False,
            "user": {"login": "dependabot[bot]"},
            "base": {"ref": "main"},
            "head": {
                "sha": self.sha,
                "repo": {"full_name": "owner/repo"},
                "ref": "dependabot/update",
            },
            "mergeable_state": "clean",
        }
        self.reviews = {1: [], 2: []}
        self.calls = []
        self.inspections = 0
        self.check_calls = 0
        self.states = ["SUCCESS"]
        self.fail_after_approval = False
        self.error_after_approval = False
        self.optional_change = None

    def own(self, id=10):
        return {
            "id": id,
            "user": {"login": "github-actions[bot]"},
            "body": self.body,
            "state": "APPROVED",
            "commit_id": self.sha,
        }

    def api(self, path, **fields):
        number = int(path.split("/pulls/")[1].split("/")[0])
        self.calls.append((path, fields))
        if path.endswith("/dismissals"):
            id = int(path.split("/reviews/")[1].split("/")[0])
            for review in self.reviews[number]:
                if review["id"] == id:
                    review["state"] = "DISMISSED"
            return {}
        if path.endswith("/reviews"):
            review = self.own()
            self.reviews[number].append(review)
            return copy.deepcopy(review)
        if path.endswith("/merge"):
            return {"merged": True}
        return {**copy.deepcopy(self.pr), "number": number}

    def pages(self, path):
        number = int(path.split("/")[-2])
        if path.endswith("/reviews"):
            return copy.deepcopy(self.reviews[number])
        return [
            {
                "author_association": "OWNER",
                "body": f"@codex review\n<!-- codex-review-head:{self.sha} -->",
            }
        ]

    def inspect(self, repo, number):
        self.inspections += 1
        if self.error_after_approval and self.reviews[number]:
            raise RuntimeError("Inspection API failed")
        return (
            self.sha,
            "pending"
            if self.fail_after_approval and self.reviews[number]
            else "success",
            "pending",
        )

    def checks(self, number):
        self.check_calls += 1
        if self.optional_change and self.inspections >= 2:
            return self.optional_change
        return self.states

    def run_queue(self, count=1):
        return reconcile(
            "owner/repo",
            [{**self.pr, "number": n} for n in range(1, count + 1)],
            self.api,
            self.pages,
            self.checks,
            self.inspect,
            self.api,
        )

    def test_optional_failure_or_rerun_after_final_inspection_revokes_approval(self):
        for states in (["SUCCESS", "FAILURE"], ["SUCCESS", "IN_PROGRESS"]):
            with self.subTest(states=states):
                self.setUp()
                self.optional_change = states
                self.run_queue()
                self.assertEqual(self.check_calls, 3)
                self.assertEqual(self.reviews[1][0]["state"], "DISMISSED")
                self.assertFalse(any(p.endswith("/merge") for p, _ in self.calls))

    def test_new_findings_after_approval_revoke_it(self):
        self.fail_after_approval = True
        self.run_queue()
        self.assertEqual(self.reviews[1][0]["state"], "DISMISSED")
        self.assertFalse(any(p.endswith("/merge") for p, _ in self.calls))

    def test_inspection_exception_after_approval_revokes_it(self):
        self.error_after_approval = True
        with self.assertRaisesRegex(RuntimeError, "Inspection API failed"):
            self.run_queue()
        self.assertEqual(self.reviews[1][0]["state"], "DISMISSED")

    def test_previous_run_approval_is_revoked_even_behind_pending_queue_candidate(self):
        self.reviews[2] = [self.own()]
        self.states = ["PENDING"]
        self.run_queue(count=2)
        self.assertEqual(self.reviews[2][0]["state"], "DISMISSED")
        self.assertFalse(any(p.endswith("/merge") for p, _ in self.calls))

    def test_unknown_prior_evidence_revokes_approval_and_fails_run(self):
        self.reviews[1] = [self.own()]
        self.error_after_approval = True
        with self.assertRaisesRegex(RuntimeError, "own approvals revoked"):
            self.run_queue()
        self.assertEqual(self.reviews[1][0]["state"], "DISMISSED")

    def test_cleanup_preserves_human_and_unrelated_actions_reviews(self):
        human = {**self.own(11), "user": {"login": "maintainer"}}
        unrelated = {**self.own(12), "body": "Another workflow approval"}
        self.reviews[1] = [self.own(), human, unrelated]
        self.states = ["FAILURE"]
        self.run_queue()
        self.assertEqual(
            [r["state"] for r in self.reviews[1]], ["DISMISSED", "APPROVED", "APPROVED"]
        )

    def test_legacy_approval_is_replaced_only_after_clean_review(self):
        from dependabot_reconcile import LEGACY_APPROVAL

        self.reviews[1] = [{**self.own(90), "body": LEGACY_APPROVAL}]
        self.run_queue()
        self.assertEqual(self.reviews[1][0]["state"], "DISMISSED")
        self.assertEqual(self.reviews[1][1]["body"], self.body)

    def test_legacy_approval_removed_while_ci_pending(self):
        from dependabot_reconcile import LEGACY_APPROVAL

        self.reviews[2] = [{**self.own(90), "body": LEGACY_APPROVAL}]
        self.states = ["PENDING"]
        self.run_queue(count=2)
        self.assertEqual(self.reviews[2][0]["state"], "DISMISSED")
        self.assertFalse(any(p.endswith("/merge") for p, _ in self.calls))

    def test_old_coderabbit_policy_approval_is_revoked_before_pending_stop(self):
        from dependabot_reconcile import CODERABBIT_APPROVAL

        self.reviews[2] = [{**self.own(90), "body": CODERABBIT_APPROVAL}]
        self.states = ["PENDING"]
        self.run_queue(count=2)
        self.assertEqual(self.reviews[2][0]["state"], "DISMISSED")
        self.assertFalse(any(p.endswith("/merge") for p, _ in self.calls))

    def test_valid_previous_approval_merges_without_duplicate_or_dismissal(self):
        self.reviews[1] = [self.own()]
        self.run_queue()
        self.assertTrue(any(p.endswith("/merge") for p, _ in self.calls))
        self.assertFalse(any(p.endswith("/dismissals") for p, _ in self.calls))
        self.assertEqual(len(self.reviews[1]), 1)

    def test_changed_base_revokes_previous_approval_without_new_mutation(self):
        self.reviews[1] = [self.own()]
        self.pr["base"]["ref"] = "other"
        self.run_queue()
        self.assertEqual(self.reviews[1][0]["state"], "DISMISSED")
        self.assertFalse(any(p.endswith("/merge") for p, _ in self.calls))


class WorkflowContinuationTests(unittest.TestCase):
    def test_production_entry_point_inspects_codex_and_live_review_activity(self):
        from unittest.mock import patch

        import dependabot_reconcile as continuation

        with (
            patch.dict("os.environ", {"GITHUB_REPOSITORY": "owner/repo"}, clear=True),
            patch.object(continuation.gate, "pages", return_value=[]),
            patch.object(continuation, "reconcile", return_value=[]) as reconcile,
        ):
            continuation.main()
        self.assertIs(reconcile.call_args.args[5], continuation.gate.inspect)
        self.assertIs(
            reconcile.call_args.kwargs["review_history"],
            continuation.gate.review_history,
        )

    def test_every_pr_ci_workflow_can_resume_the_queue(self):
        import re

        directory = Path(__file__).resolve().parents[2] / ".github" / "workflows"
        continuation = (directory / "dependabot-continuation.yml").read_text()
        match = re.search(r"workflows: \[([^\]]+)\]", continuation)
        self.assertIsNotNone(match)
        triggers = {name.strip() for name in match[1].split(",")}
        for workflow in directory.glob("*.yml"):
            content = workflow.read_text()
            if re.search(r"^  pull_request(?:_target)?:", content, re.MULTILINE):
                name = re.search(r"^name: (.+)$", content, re.MULTILINE)[1]
                with self.subTest(workflow=workflow.name):
                    self.assertIn(name, triggers)

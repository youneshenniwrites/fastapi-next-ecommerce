import unittest
from unittest.mock import patch

from scripts import codex_review_gate as gate


class Publication(unittest.TestCase):
    def run_gate(
        self,
        heads,
        outcomes,
        repeat=1,
        only_pr=None,
        fail_publish=None,
        fail_history=False,
    ):
        self.statuses = []
        self.errors = []
        history = {}
        pulls = [{"number": n, "head": {"sha": sha}} for n, sha in heads.items()]

        def api(path, data=None):
            if "/commits/" in path:
                if fail_history:
                    raise RuntimeError("Status history unavailable")
                return history.get(path.split("/commits/")[1].split("/")[0], [])
            if "/statuses/" in path:
                if path.rsplit("/", 1)[-1] == fail_publish:
                    raise RuntimeError("Status write failed")
                self.statuses.append((path.rsplit("/", 1)[-1], data["state"]))
                history[path.rsplit("/", 1)[-1]] = [dict(data)]
                return {}
            return {
                "head": {"sha": heads[int(path.rsplit("/", 1)[-1])]},
                "state": "open",
                "draft": False,
            }

        def inspect(repo, number):
            value = outcomes[number]
            if isinstance(value, Exception):
                raise value
            return (
                value
                if isinstance(value, tuple)
                else (heads[number], value, "test evidence")
            )

        with (
            patch.dict("os.environ", {}, clear=True),
            patch.object(gate, "pages", return_value=pulls),
            patch.object(gate, "api", side_effect=api),
            patch.object(gate, "inspect", side_effect=inspect),
            patch.object(gate, "report"),
            patch(
                "sys.argv",
                [
                    "gate",
                    "--repo",
                    "owner/repo",
                    "--publish",
                    "--details-url",
                    "https://github.com/owner/repo/actions/runs/1",
                ],
            ),
        ):
            for _ in range(repeat):
                try:
                    gate.publish_reviews(
                        "owner/repo",
                        "https://github.com/owner/repo/actions/runs/1",
                        only_pr,
                    )
                except RuntimeError as error:
                    self.errors.append(error)

    def test_api_failure_does_not_leave_other_heads_with_old_success(self):
        self.run_gate(
            {1: "a" * 40, 2: "b" * 40},
            {1: RuntimeError("API unavailable"), 2: "pending"},
        )
        self.assertIn(("b" * 40, "pending"), self.statuses)

    def test_prs_sharing_a_commit_cannot_overwrite_pending_with_success(self):
        self.run_gate({1: "a" * 40, 2: "a" * 40}, {1: "pending", 2: "success"})
        self.assertEqual(self.statuses[-1], ("a" * 40, "pending"))

    def test_all_prs_sharing_commit_must_pass(self):
        self.run_gate({1: "a" * 40, 2: "a" * 40}, {1: "success", 2: "success"})
        self.assertEqual(self.statuses[-1], ("a" * 40, "success"))

    def test_repeated_success_does_not_exhaust_status_limit(self):
        self.run_gate({1: "a" * 40}, {1: "success"}, repeat=1001)
        self.assertEqual(self.statuses, [("a" * 40, "success")])

    def test_scoped_refresh_includes_sibling_prs_with_same_sha(self):
        self.run_gate(
            {1: "a" * 40, 2: "a" * 40}, {1: "success", 2: "pending"}, only_pr=1
        )
        self.assertEqual(self.statuses[-1], ("a" * 40, "pending"))

    def test_changed_head_is_never_published_as_success(self):
        self.run_gate({1: "a" * 40}, {1: ("b" * 40, "success", "changed")})
        self.assertEqual(self.statuses, [("a" * 40, "pending")])

    def test_failed_inspection_fails_run_and_still_processes_other_prs(self):
        self.run_gate(
            {1: "a" * 40, 2: "b" * 40}, {1: RuntimeError("API"), 2: "success"}
        )
        self.assertEqual(len(self.errors), 1)
        self.assertIn(("a" * 40, "pending"), self.statuses)
        self.assertIn(("b" * 40, "success"), self.statuses)

    def test_failed_publication_does_not_abandon_other_heads(self):
        self.run_gate(
            {1: "a" * 40, 2: "b" * 40},
            {1: "success", 2: "pending"},
            fail_publish="a" * 40,
        )
        self.assertEqual(len(self.errors), 1)
        self.assertIn(("b" * 40, "pending"), self.statuses)

    def test_missing_status_history_cannot_publish_success(self):
        self.run_gate({1: "a" * 40}, {1: "success"}, fail_history=True)
        self.assertEqual(self.statuses, [("a" * 40, "pending")])
        self.assertEqual(len(self.errors), 1)

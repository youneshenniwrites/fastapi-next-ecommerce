"""Trusted status publication rejects invalid and concurrently changed PRs."""

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_branch_name
from scripts.tests.test_branch_name import event

sys.modules["check_branch_name"] = check_branch_name
spec = importlib.util.spec_from_file_location(
    "publish_branch_name", Path(__file__).parents[1] / "publish_branch_name.py"
)
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class Publication(unittest.TestCase):
    def run_case(self, branches=None, changed=None):
        import copy

        prs = []
        for number, branch in enumerate(branches or ["feat/vin-118-orders"], 180):
            pr = event(branch)["pull_request"]
            pr.update(state="open", number=number)
            pr["head"]["sha"] = "a" * 40
            prs.append(pr)
        statuses = []

        def api(path, payload=None):
            if path.startswith("statuses/"):
                statuses.append(payload)
                return {}
            if path.startswith("issues/"):
                return {"number": 118}
            result = copy.deepcopy(prs)
            if changed == "title":
                result[0]["title"] = "[VIN-119] [feat] Different"
            elif changed == "new":
                extra = copy.deepcopy(result[0])
                extra["number"] = 999
                extra["head"]["ref"] = "invalid"
                result.append(extra)
            elif changed == "closed":
                result.pop()
            elif changed == "head":
                result[0]["head"]["sha"] = "b" * 40
            return result

        with (
            patch.object(publisher, "api", side_effect=api),
            patch.dict(
                "os.environ",
                {"GITHUB_SERVER_URL": "https://github.com", "GITHUB_RUN_ID": "1"},
            ),
        ):
            publisher.publish("a" * 40, prs)
        return [s["state"] for s in statuses]

    def test_valid_head(self):
        self.assertEqual(self.run_case(), ["pending", "success"])

    def test_bad_branch_fails(self):
        self.assertEqual(self.run_case(["feat/no-ticket"]), ["pending", "failure"])

    def test_changed_group_cannot_get_success(self):
        for change in ("title", "new", "closed", "head"):
            with self.subTest(change=change):
                self.assertEqual(self.run_case(changed=change), ["pending", "pending"])

    def test_shared_sha_invalid_sibling_blocks_in_either_order(self):
        for branches in (
            ["feat/vin-118-orders", "invalid"],
            ["invalid", "feat/vin-118-orders"],
        ):
            with self.subTest(branches=branches):
                self.assertEqual(self.run_case(branches), ["pending", "failure"])

    def test_all_valid_shared_sha(self):
        self.assertEqual(
            self.run_case(["feat/vin-118-orders", "test/vin-118-orders"]),
            ["pending", "success"],
        )

    def test_paginates_open_prs(self):
        with patch.object(publisher, "api", side_effect=[[{}] * 100, [{}]]) as api:
            self.assertEqual(len(publisher.open_prs()), 101)
            self.assertEqual(
                api.call_args.args[0], "pulls?state=open&per_page=100&page=2"
            )

    def test_main_publishes_once_per_distinct_sha(self):
        prs = [{"head": {"sha": sha}} for sha in ("a", "a", "b")]
        with (
            patch.object(publisher, "open_prs", return_value=prs),
            patch.object(publisher, "publish") as publish,
        ):
            publisher.main()
        self.assertEqual(publish.call_count, 2)
        publish.assert_any_call("a", prs)
        publish.assert_any_call("b", prs)

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
    def run_case(self, branch="feat/vin-118-order-drafts", changed=False):
        pr = event(branch)["pull_request"]
        pr["state"] = "open"
        pr["head"]["sha"] = "a" * 40
        statuses = []
        reads = 0

        def api(path, payload=None):
            nonlocal reads
            if path.startswith("statuses/"):
                statuses.append(payload)
                return {}
            if path.startswith("issues/"):
                return {"number": 118}
            reads += 1
            import copy

            result = copy.deepcopy(pr)
            if changed and reads > 1:
                result["title"] = "[VIN-119] [feat] Different"
            return result

        with (
            patch.object(publisher, "api", side_effect=api),
            patch.dict(
                "os.environ",
                {"GITHUB_SERVER_URL": "https://github.com", "GITHUB_RUN_ID": "1"},
            ),
        ):
            publisher.publish(179)
        return [s["state"] for s in statuses]

    def test_valid_head(self):
        self.assertEqual(self.run_case(), ["pending", "success"])

    def test_bad_branch_fails(self):
        self.assertEqual(self.run_case("feat/no-ticket"), ["pending", "failure"])

    def test_changed_title_cannot_get_success(self):
        self.assertEqual(self.run_case(changed=True), ["pending", "pending"])

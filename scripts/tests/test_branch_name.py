"""Branch naming covers human PRs, narrow legacy support and bot impersonation."""

import unittest

from scripts.check_branch_name import validate


def event(branch="feat/vin-118-order-drafts", title="[VIN-118] [feat] Add drafts"):
    return {
        "pull_request": {
            "number": 179,
            "title": title,
            "user": {"id": 1, "login": "human", "type": "User"},
            "head": {
                "ref": branch,
                "repo": {"full_name": "youneshenniwrites/fastapi-next-ecommerce"},
            },
        }
    }


class BranchNames(unittest.TestCase):
    def test_valid(self):
        for kind in (
            "feat",
            "fix",
            "docs",
            "test",
            "ci",
            "build",
            "chore",
            "refactor",
            "perf",
            "style",
            "revert",
        ):
            self.assertIn(
                "valid",
                validate(event(f"{kind}/vin-118-drafts"), lambda n: {"number": n}),
            )

    def test_invalid(self):
        for name in (
            "feat/order-drafts",
            "feat/vin-0-test",
            "feat/VIN-118-test",
            "feat/vin-118-test--bad",
            "feat/vin-118-test;echo",
            "dependabot/npm/test",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                validate(event(name), lambda n: {"number": n})

    def test_title_mismatch_and_pr_number(self):
        with self.assertRaises(ValueError):
            validate(event(title="[VIN-119] [feat] Drafts"), lambda n: {"number": n})
        with self.assertRaises(ValueError):
            validate(event(), lambda n: {"number": n, "pull_request": {}})

    def test_dependabot_identity(self):
        e = event("dependabot/npm/patches")
        e["pull_request"]["user"] = {
            "id": 49699333,
            "login": "dependabot[bot]",
            "type": "Bot",
        }
        self.assertIn(
            "Dependabot", validate(e, lambda n: self.fail("No issue required"))
        )
        e["pull_request"]["user"]["id"] = 1
        with self.assertRaises(ValueError):
            validate(e, lambda n: {})

    def test_grandfather_is_exact(self):
        e = event("feat/order-drafts")
        e["pull_request"]["number"] = 177
        self.assertIn("Existing", validate(e, lambda n: {}))
        e["pull_request"]["number"] = 180
        with self.assertRaises(ValueError):
            validate(e, lambda n: {})

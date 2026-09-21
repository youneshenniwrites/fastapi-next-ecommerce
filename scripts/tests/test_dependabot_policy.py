"""Regression cases for the privileged automation boundary."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dependabot_policy import eligible


class DependencyPolicyTests(unittest.TestCase):
    def setUp(self):
        self.pr = {"state": "open", "draft": False, "user": {"login": "dependabot[bot]"}, "base": {"ref": "main"}, "head": {"repo": {"full_name": "owner/repo"}, "ref": "dependabot/npm/update"}}
        self.files = [{"status": "modified", "filename": "frontend/package-lock.json"}]
        self.commits = [{"author": {"login": "dependabot[bot]"}, "commit": {"verification": {"verified": True}}}]

    def check(self, ecosystem="npm", update="version-update:semver-patch"):
        return eligible(self.pr, self.files, self.commits, ecosystem, update, "owner/repo")

    def test_patch_and_minor(self):
        self.assertTrue(self.check())
        self.assertTrue(self.check(update="version-update:semver-minor"))

    def test_major_and_unknown(self):
        for kind in ["version-update:semver-major", "", "unknown"]:
            self.assertFalse(self.check(update=kind))
        self.assertFalse(self.check(ecosystem="github-actions"))

    def test_untrusted_author_fork_draft_or_base(self):
        original = copy.deepcopy(self.pr)
        for path, value in [(('user', 'login'), 'someone'), (('head', 'repo', 'full_name'), 'fork/repo'), (('base', 'ref'), 'other'), (('draft',), True)]:
            self.pr = copy.deepcopy(original)
            target = self.pr
            for key in path[:-1]: target = target[key]
            target[path[-1]] = value
            self.assertFalse(self.check())

    def test_unexpected_or_renamed_files(self):
        self.files.append({"status": "modified", "filename": ".github/workflows/ci.yml"})
        self.assertFalse(self.check())
        self.files = [{"status": "renamed", "filename": "frontend/package-lock.json"}]
        self.assertFalse(self.check())
        self.files = []
        self.assertFalse(self.check())

    def test_human_or_unsigned_commit(self):
        self.commits[0]['author']['login'] = 'owner'
        self.assertFalse(self.check())
        self.commits[0]['author']['login'] = 'dependabot[bot]'
        self.commits[0]['commit']['verification']['verified'] = False
        self.assertFalse(self.check())

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
        self.commits = [{"author": {"login": "dependabot[bot]"}, "committer": {"login": "web-flow"}, "commit": {"verification": {"verified": True}}}]

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

    def test_spoofed_author_with_human_signer_is_rejected(self):
        self.commits[0]["committer"] = {"login": "collaborator"}
        self.assertFalse(self.check())
        self.commits[0]["committer"] = None
        self.assertFalse(self.check())


class AtomicMergeTests(unittest.TestCase):
    def run_merge(self, head="reviewed", states=None, merge_error=False):
        from dependabot_merge import merge_validated
        calls = []
        def api(path, **fields):
            calls.append((path, fields))
            if path.endswith('/merge'):
                if merge_error:
                    raise RuntimeError('409 head changed')
                return {'merged': True}
            if path.endswith('/reviews'): return {}
            return {'state': 'open', 'draft': False, 'head': {'sha': head}}
        result = merge_validated('owner/repo', 1, 'reviewed', api,
                                 lambda: states if states is not None else ['SUCCESS'],
                                 sleep=lambda _: None)
        return result, calls

    def test_changed_head_never_approved_or_merged(self):
        result, calls = self.run_merge(head='replacement')
        self.assertEqual(len(calls), 1)
        self.assertIn('no merge', result)

    def test_exact_sha_sent_to_atomic_merge(self):
        _, calls = self.run_merge()
        self.assertEqual(calls[-1][1]['sha'], 'reviewed')
        self.assertEqual(calls[-2][1]['commit_id'], 'reviewed')

    def test_late_push_rejection_is_not_retried_on_new_head(self):
        with self.assertRaisesRegex(RuntimeError, '409'):
            self.run_merge(merge_error=True)

    def test_failure_and_missing_checks_do_not_merge(self):
        for states in [['FAILURE'], []]:
            _, calls = self.run_merge(states=states)
            self.assertTrue(all(not fields for _, fields in calls))

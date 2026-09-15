"""Tests for development deployment eligibility."""

import tempfile
import unittest
from unittest.mock import patch

import development_ready
from development_ready import passed

SHA = "a" * 40


def run(id=1):
    """Build a successful main push workflow run fixture."""
    return {
        "id": id,
        "head_sha": SHA,
        "head_branch": "main",
        "event": "push",
        "conclusion": "success",
    }


class DevelopmentGateTests(unittest.TestCase):
    def test_requires_exact_main_push(self):
        """Require a successful workflow run for the exact main push revision."""
        self.assertTrue(passed([run()], SHA))
        for key, value in [
            ("head_sha", "b" * 40),
            ("head_branch", "feature"),
            ("event", "pull_request"),
            ("conclusion", "failure"),
            ("conclusion", None),
        ]:
            candidate = run()
            candidate[key] = value
            self.assertFalse(passed([candidate], SHA))
        self.assertFalse(passed([], SHA))

    def test_new_failed_or_pending_run_invalidates_old_success(self):
        """Reject a revision when its latest run failed or remains pending."""
        for conclusion in ["failure", None]:
            latest = run(id=2)
            latest["conclusion"] = conclusion
            self.assertFalse(passed([latest, run()], SHA))

    def evaluate(self, missing=None, deployed=False, current=SHA):
        """Run the eligibility entry point against controlled GitHub responses."""

        def api(path):
            """Return a response fixture based on the requested GitHub API path."""
            if path.endswith("commits/main"):
                return {"sha": current}
            if "/actions/workflows/" in path:
                return {"workflow_runs": [] if missing and missing in path else [run()]}
            if "/statuses?" in path:
                return [{"state": "success"}]
            if "environment=development" in path:
                return [{"id": 12}] if deployed else []
            return []

        with tempfile.NamedTemporaryFile(mode="r+") as output:
            with (
                patch.dict(
                    "os.environ",
                    {
                        "GITHUB_REPOSITORY": "owner/repo",
                        "CANDIDATE_SHA": SHA,
                        "GITHUB_OUTPUT": output.name,
                    },
                ),
                patch.object(development_ready, "api", side_effect=api),
            ):
                development_ready.main()
            output.seek(0)
            return output.read()

    def test_deploys_verified_main_revision_once(self):
        """Allow only the current fully verified revision before its first deploy."""
        self.assertIn("ready=true", self.evaluate())
        self.assertIn("ready=false", self.evaluate(current="b" * 40))
        self.assertIn("ready=false", self.evaluate(missing="ci.yml"))
        self.assertIn("ready=false", self.evaluate(deployed=True))


if __name__ == "__main__":
    unittest.main()
